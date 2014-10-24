import redis
import gevent.socket
import gevent.threading
import redis.connection
redis.connection.socket = gevent.socket
redis.connection.threading = gevent.threading

import random, string, json
import logging
from zerorpc.exceptions import TimeoutExpired, RemoteError, LostRemote

from .event import Event


def get_host_port(endpoint):
    if not endpoint[:8] == 'redis://':
        raise ValueError("Redis backend does not support endpoint %s" % endpoint)
    host, port = endpoint[8:].split('/')[0].split(':')
    if len(host) == 0: host = 'localhost'
    if len(port) == 0: port = 6379
    return host, port

def get_queue(endpoint):
    parts = endpoint[8:].split('/')
    return parts[1] if len(parts) > 1 else None

def random_string(size=8, chars=string.ascii_uppercase + string.digits):
    """Ref: http://stackoverflow.com/questions/2257441"""
    return ''.join(random.choice(chars) for x in xrange(size))


class FunctionCall(dict):
    """Encapsulates a function call as a Python dictionary."""

    @staticmethod
    def from_dict(dictionary):
        """Return a new FunctionCall from a Python dictionary."""
        name = dictionary.get('name')
        args = dictionary.get('args')
        kwargs = dictionary.get('kwargs')
        return FunctionCall(name, args, kwargs)

    def __init__(self, name, args=None, kwargs=None):
        """Create a new FunctionCall from a method name, an optional argument tuple, and an optional keyword argument
        dictionary."""
        self['name'] = name
        if args is not None and args != ():
            self['args'] = args
        if kwargs is not None and kwargs != {}:
            self['kwargs'] = kwargs

    def as_python_code(self):
        """Return a string representation of this object that can be evaled to execute the function call."""
        argstring = '' if 'args' not in self else \
                ','.join(str(arg) for arg in self['args'])
        kwargstring = '' if 'kwargs' not in self else \
                ','.join('%s=%s' % (key,val) for (key,val) in self['kwargs'].iteritems())
        if len(argstring) == 0:
            params = kwargstring
        elif len(kwargstring) == 0:
            params = argstring
        else:
            params = ','.join([argstring,kwargstring])
        return '%s(%s)' % (self['name'], params)



class Client(object):

    def __init__(self, endpoint=None, timeout=30):
        self._redis = None
        self._queue = None
        self._timeout = timeout
        if endpoint != None:
            self.connect(endpoint)

    def connect(self, endpoint):
        host, port = get_host_port(endpoint)
        self._redis = redis.StrictRedis(host, port)
        self._queue = get_queue(endpoint)

    def __call__(self, method, *args, **kwargs):
        function_call = FunctionCall(method, args, kwargs)
        response_queue = self._queue + ':rpc:' + random_string()
        rpc_request = dict(function_call=function_call, response_queue=response_queue)
        message = json.dumps(rpc_request)
        logging.debug('RPC Request: %s' % message)

        # send request
        self._redis.rpush(self._queue, message)
        timeout = kwargs.get('timeout', self._timeout)
        result = self._redis.blpop(response_queue, timeout)
        if result is None:
            raise TimeoutExpired()

        # process reply
        queue, message = result
        assert queue == response_queue
        logging.debug('RPC Response: %s' % message)
        rpc_response = json.loads(message)
        exception = rpc_response.get('exception')
        if exception is not None:
            raise RemoteError(exception)
        if 'return_value' not in rpc_response:
            raise RemoteError('Malformed RPC Response message: %s' % rpc_response)
        return rpc_response['return_value']

    def __getattr__(self, method):
        return lambda *args, **kwargs: self(method, *args, **kwargs)

    def close(self):
        self._redis.close()


class Server(object):

    def __init__(self, methods, endpoint=None, _=None):
        self._redis = None
        self._queue = None
        self._methods = methods
        if endpoint != None:
            self.bind(endpoint)

    def bind(self, endpoint):
        host, port = get_host_port(endpoint)
        self._redis = redis.StrictRedis(host, port)
        self._queue = get_queue(endpoint)

    def run(self):
        # Flush the message queue.
        self._redis.delete(self._queue)
        while True:
            queue, message = self._redis.blpop(self._queue)
            assert queue == self._queue
            logging.debug('RPC Request: %s' % message)
            rpc_request = json.loads(message)
            response_queue = rpc_request['response_queue']
            function_call = FunctionCall.from_dict(rpc_request['function_call'])
            code = 'return_value = self._methods.' + function_call.as_python_code()
            try:
                exec(code)
                rpc_response = dict(return_value=return_value)
            except:
                (type, value, traceback) = sys.exc_info()
                rpc_response = dict(exception=repr(value))
            message = json.dumps(rpc_response)
            logging.debug('RPC Response: %s' % message)
            self._redis.rpush(response_queue, message)

    def close(self):
        self._redis.close()


class Publisher(object):

    def __init__(self, endpoint=None, _=None):
        self._redis = None
        if endpoint != None: self.bind(endpoint)

    def bind(self, endpoint):
        host, port = get_host_port(endpoint)
        self._redis = redis.StrictRedis(host, port)

    def publish(self, channel, data):
        self._redis.publish(channel, data)

    def transport(self):
        return self._redis

    def close(self):
        self._redis.close()


class Subscriber(object):

    def __init__(self, endpoint=None, _=None):
        self._redis = None
        self._subs = None
        self.on_receive = {}
        if endpoint != None: self.connect(endpoint)

    def connect(self, endpoint):
        host, port = get_host_port(endpoint)
        self._redis = redis.StrictRedis(host, int(port))
        self._subs = self._redis.pubsub()

    def subscribe(self, channel, handler=None):
        self._subs.psubscribe(channel)
        if handler:
            if callable(handler):
                handlers = self.on_receive.get(channel, Event())
                handlers.on(handler)
                self.on_receive[channel] = handlers
            else:
                raise ValueError('invalid handler')

       # consume the confirmation
        return self._subs.listen().next()

    def unsubscribe(self, channel):
        self._subs.punsubscribe(channel)
        self.on_receive.pop(channel, None)

    def receive(self):
        msg = self._subs.listen().next()
        yield msg['channel'], msg['data']

    def transport(self):
        return self._redis

    def run(self):
        for channel, data in self.receive():
            handlers = self.on_receive.get(channel, Event())
            handlers(channel, data)

    def close(self):
        self._redis.close()
