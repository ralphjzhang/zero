import zero
import gevent
import gevent_zmq as zmq
import threading

ctx = zmq.Context()

def test_redis_rpc_1():
    class Hello:
        def hello(self):
            return 'hello, rpc'

    ep = "redis://:/rpc_test"
    s = zero.Server(Hello(), ep)
    gevent.spawn(s.run)
    gevent.sleep(0.01)
    c = zero.Client(ep)
    assert c.hello() == 'hello, rpc'

def test_zerorpc_pubsub_1():
    ep = "inproc://#1"
    p = zero.Publisher(ep, ctx)
    s = zero.Subscriber(ep, ctx)
    result = ["", ""]
    def assign_result(topic, data):
        result[0], result[1] = topic, data
    s.subscribe("topic", assign_result)
    gevent.spawn(s.run)
    p.publish("topic", "data")
    gevent.sleep(0.01)
    assert result == ["topic", "data"]

def test_zerorpc_pubsub_2():
    ep = "inproc://#2"
    p = zero.Publisher(ep, ctx)
    s = zero.Subscriber(ep, ctx)
    result = ["", ""]
    def assign_result(topic, data):
        result[0], result[1] = topic, data
    s.subscribe("topic", assign_result)
    gevent.spawn(s.run)
    p.publish("topic", "data")
    p.publish("topic1", "data1")
    gevent.sleep(0.01)
    assert result == ["topic", "data"]

def test_redis_pubsub_1():
    ep = "redis://:"
    p = zero.Publisher(ep)
    s = zero.Subscriber(ep)
    result = ["", ""]
    def assign_result(topic, data):
        result[0], result[1] = topic, data
    s.subscribe('channel1', assign_result)
    p.publish("channel1", "data1")
    gevent.spawn(s.run)
    gevent.sleep(0.01)
    assert result == ["channel1", "data1"]

def test_redis_pubsub_2():
    ep = "redis://:"
    p = zero.Publisher(ep)
    s = zero.Subscriber(ep)
    result = ["", ""]
    def assign_result(topic, data):
        result[0], result[1] = topic, data
    s.subscribe('channel1', assign_result)
    p.publish("channel1", "data1")
    p.publish("channel2", "data2")
    gevent.spawn(s.run)
    gevent.sleep(0.01)
    assert result == ["channel1", "data1"]
