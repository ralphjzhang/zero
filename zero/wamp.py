from geventwebsocket.server import WebSocketServer
from geventwebsocket.resource import Resource, WebSocketApplication
from geventwebsocket.protocols.wamp import WampProtocol
from urlparse import urlparse
import json
import gevent
from gevent import monkey
monkey.patch_all()
# WebSocketApp threading/select patched to gevent
from websocket import WebSocketApp as WebSocketClient


class Server(object):

    def __init__(self, methods=None):
        self._endpoint = None
        self._methods = methods
        self._wsserver = None

    def bind(self, endpoint):
        self._endpoint = endpoint

    def run(self):
        methods = self._methods
        endpoint = self._endpoint

        class WampApplication(WebSocketApplication):
            protocol_class = WampProtocol

            def on_open(self):
                wamp = self.protocol
                if methods:
                    wamp.register_object(endpoint, methods)


        ep = urlparse(self._endpoint)
        resource = Resource({'^%s$' % ep.path: WampApplication})
        self._wsserver = WebSocketServer(ep.netloc, resource, debug=True)
        self._wsserver.serve_forever()


class Client(object):

    def __init__(self):
        self._endpoint = None
        # we actually just use the constant definitions
        self._wamp = WampProtocol(None)
        self._ws = None
        self._session_id = None

    def connect(self, endpoint):
        self._endpoint = endpoint
        self._ws = WebSocketClient(self._endpoint, on_message=self._on_message)
        gevent.spawn(self._ws.run_forever, None, None, 10)

    def _on_message(self, sock, data):
        if data[0] == self._wamp.MSG_WELCOME and len(data) > 1:
            self._session_id = data[1]
        elif data[0] == self._wamp.MSG_CALL_RESULT:
            # TODO
            pass
        elif data[0] == self._wamp.MSG_CALL_ERROR:
            # TODO
            pass
        else:
            raise Exception('Unexpected message received')

    def __call__(self):
        pass


class Publisher():
    
    def __init__(self):
        self._endpoint = None
        self._wsserver = None
        self._wsclient = None

    def bind(self, endpoint):
        self._endpoint = endpoint

        class WampApplication(WebSocketApplication):
            protocol_class = WampProtocol

            def on_open(self):
                wamp = self.protocol
                wamp.register_pubsub('http://topic1')


        ep = urlparse(self._endpoint)
        resource = Resource({'^%s$' % ep.path: WampApplication})
        self._wsserver = WebSocketServer(ep.netloc, resource, debug=True)
        gevent.spawn(self._wsserver.serve_forever)
        self._wsclient = WebSocketClient(self._endpoint)
        gevent.spawn(self._wsclient.run_forever)

    def publish(self, topic, message):
        data = json.dumps([WampProtocol.MSG_PUBLISH, topic, message])
        print data
        self._wsclient.send(data)


class Subscriber():

    def __init__(self):
        self._endpoint = None
        # we actually just use the constant definitions
        self._wamp = WampProtocol(None)
        self._ws = None
        self._session_id = None
        self._handlers_table = {'': set()}
        self._received = list()

    def connect(self, endpoint):
        self._endpoint = endpoint
        self._ws = WebSocketClient(self._endpoint, on_message=self._on_message)
        gevent.spawn(self._ws.run_forever, None, None, 10)

    def subscribe(self, topic, handler):
        #self._ws.send(json.dumps([self._wamp.MSG_PREFIX, topic.split(':')[0], topic]))
        self._ws.send(json.dumps([self._wamp.MSG_SUBSCRIBE, topic]))
        # TODO wait for SUBSCRIBED
        if handler:
            self._add_handler(topic, handler)

    def unsubscribe(self, topic):
        self._ws.send([self._wamp.MSG_UNSUBSCRIBE, topic])
        # TODO wait for UNSUBSCRIBED
        return self._handlers_table.pop(topic, set())

    def receive(self):
        return self._received.pop(0)

    def run(self):
        self._ws = WebSocketClient(self._endpoint, on_message=self._on_message)
        gevent.spawn(self._receiver)
        gevent.spawn(self._ws.run_forever, None, None, 10)

    def _receiver(self):
        while True:
            topic, message = self.receive()
            handlers = self._handlers_table.get(topic, set())
            for handler in handlers:
                handler(topic, message)

    def _on_message(self, sock, msg):
        data = json.loads(msg)
        if data[0] == self._wamp.MSG_WELCOME and len(data) > 1:
            self._session_id = data[1]
        elif data[0] == self._wamp.MSG_EVENT and len(data) >= 3:
            topic, message = data[1], data[2]
            # TODO list length limit
            self.received.append((topic, message))
        else:
            raise Exception('Unexpected message received')

    def _add_handler(self, topic, handler):
        def _add_topic_handler(topic, handler):
            handlers = self._handlers_table.get(topic, set())
            handlers |= set([handler])
            self._handlers_table[topic] = handlers

        if callable(handler):
            if topic == '':
                for tpc in self._handlers_table.keys():
                    _add_topic_handler(tpc, handler)
            else:
                _add_topic_handler(topic, handler)
        else:
            raise ValueError('invalid handler')



