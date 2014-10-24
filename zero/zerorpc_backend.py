import gevent_zmq as zmq
import zerorpc
import umsgpack as msgpack

from zerorpc import Client, Server
from .event import Event

class Subscriber(object):

    def __init__(self, endpoint=None, context=None):
        self._context = context or zmq.Context()
        self._socket = zmq.Socket(self._context, zmq.SUB)
        self._socket.setsockopt(zmq.UNSUBSCRIBE, '')
        self.on_receive = {}
        if endpoint != None: self.connect(endpoint)

    def connect(self, endpoint):
        self._socket.connect(endpoint)

    def subscribe(self, topic, handler=None):
        self._socket.setsockopt(zmq.SUBSCRIBE, topic)
        if handler:
            if callable(handler):
                handlers = self.on_receive.get(topic, Event())
                handlers.on(handler)
                self.on_receive[topic] = handlers
            else:
                raise ValueError('invalid handler')

    def unsubscribe(self, topic):
        self._socket.setsockopt(zmq.UNSUBSCRIBE, topic)
        self.on_receive.pop(topic, None)

    def receive(self):
        event = self._socket.recv_multipart()
        topic, message = event[0], msgpack.loads(event[1])
        yield topic, message

    def run(self):
         for topic, message in self.receive():
            handlers = self.on_receive.get(topic, Event())
            handlers(topic, message)

    def transport(self):
        return self._socket

    def close(self):
        self._socket.close()


class Publisher(object):

    def __init__(self, endpoint=None, context=None):
        self._context = context or zmq.Context()
        self._socket = zmq.Socket(self._context, zmq.PUB)
        if endpoint != None: self.bind(endpoint)

    def bind(self, endpoint):
        self._socket.bind(endpoint)

    def publish(self, topic, message):
        self._socket.send_multipart((topic, msgpack.dumps(message)))

    def transport(self):
        return self._socket

    def close(self):
        self._socket.close()
