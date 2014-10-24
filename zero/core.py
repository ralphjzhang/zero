import zerorpc_backend as zerorpc
import redis_backend as redis
from urlparse import urlparse

# TODO integrate WAMP/crossbar

import logging
logging.basicConfig()

def get_backend(endpoint):
    ep = urlparse(endpoint)
    if ep.scheme in ['redis']:
        return redis
    elif ep.scheme in ['tcp', 'ipc', 'inproc', 'pgm']:
        return zerorpc
    else:
        raise ValueError("Unknown backend for endpoint %s" % s)

# TODO factory method creating node
def create_node(endpoint, settings):
    pass

class Node(object):
    pass


class Client(object):

    def __init__(self, endpoint=None, options=None):
        self._backend = None
        self._options = options
        if endpoint != None: self.connect(endpoint)

    def connect(self, endpoint):
        self._backend = get_backend(endpoint).Client(endpoint, self._options)

    def __call__(self, method, *args, **kwargs):
        return self.__call__(method, *args, **kwargs)

    def __getattr__(self, method):
        return self._backend.__getattr__(method)

    def close(self):
        self._backend.close()


class Server(object):

    def __init__(self, methods, endpoint=None, options=None):
        self._backend = None
        self._methods = methods
        self._options = options
        if endpoint != None: self.bind(endpoint)

    def bind(self, endpoint):
        self._backend = get_backend(endpoint).Server(self._methods, endpoint, self._options)

    def run(self):
        return self._backend.run()


class Publisher(object):

    def __init__(self, endpoint=None, options=None):
        self._backend = None
        self._options = options
        if endpoint != None: self.bind(endpoint)

    def bind(self, endpoint):
        self._backend = get_backend(endpoint).Publisher(endpoint, self._options)

    def publish(self, channel, data):
        self._backend.publish(channel, data)

    def transport(self):
        return self._backend.transport()

    def close(self):
        self._backend.close()


class Subscriber:

    def __init__(self, endpoint=None, options=None):
        self._backend = None
        self._options = options
        if endpoint != None: self.connect(endpoint)

    def connect(self, endpoint):
        self._backend = get_backend(endpoint).Subscriber(endpoint, self._options)

    def subscribe(self, channel, handler=None):
        return self._backend.subscribe(channel, handler)

    def unsubscribe(self, channel, handler=None):
        return self._backend.unsubscribe(channel, handler)

    def receive(self):
        return self._backend.receive()

    def run(self):
        return self._backend.run()

    def transport(self):
        return self._backend.transport()

    def close(self):
        self._backend.close()
