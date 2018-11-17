from autobahn.twisted import WebSocketClientProtocol, WebSocketClientFactory, \
    WebSocketServerFactory
from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from carly import Context, hookMethod
from .autobahn_websocket import MyServerProtocol


class TestLineReceiverServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        server = context.makeTCPServer(MyServerProtocol, WebSocketServerFactory())
        client = context.makeTCPClient(WebSocketClientProtocol, server.port, WebSocketClientFactory(), when='onOpen')
        hookMethod(client.protocolClass, 'onMessage', decoder=lambda payload, _: payload)
        self.client = yield client.protocol
        self.addCleanup(context.cleanup)

    def testConnectDisconnect(self):
        pass

    @inlineCallbacks
    def testDisconnectDuringTest(self):
        self.client.sendMessage(b'hello', isBinary=True)
        yield self.client.connectionLost.called()

    @inlineCallbacks
    def testOneMessage(self):
        self.client.sendMessage(b'hello')
        payload = yield self.client.onMessage.called()
        compare(payload, expected='hello')

    @inlineCallbacks
    def testSendMessageReceiveMessageSendMessageRecieveMessage(self):
        self.client.sendMessage(b'hello')
        payload = yield self.client.onMessage.called()
        compare(payload, expected='hello')
        self.client.sendMessage(b'goodbye')
        payload = yield self.client.onMessage.called()
        compare(payload, expected='goodbye')

    @inlineCallbacks
    def testSendTwoMessagesReceveBoth(self):
        self.client.sendMessage(b'hello')
        self.client.sendMessage(b'goodbye')
        payload = yield self.client.onMessage.called()
        compare(payload, expected='hello')
        payload = yield self.client.onMessage.called()
        compare(payload, expected='goodbye')
