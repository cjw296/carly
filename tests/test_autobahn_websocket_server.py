from autobahn.twisted import WebSocketClientProtocol, WebSocketServerFactory
from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from carly import Context, hook
from carly.tcp import makeTCPServer
from carly.websocket import makeWebSocketClient
from .autobahn_websocket import MyServerProtocol


class TestWebSocketServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        server = makeTCPServer(context, MyServerProtocol, WebSocketServerFactory())
        client = yield makeWebSocketClient(context, server)
        hook(WebSocketClientProtocol, 'onMessage', decoder=lambda payload, _: payload)
        self.client = client.clientProtocol
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
