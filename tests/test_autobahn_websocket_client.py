from autobahn.twisted import WebSocketClientFactory, WebSocketServerFactory, WebSocketServerProtocol
from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from carly import Context, hook, cancelDelayedCalls, advanceTime
from .autobahn_websocket import MyClientProtocol


class TestWebSocketClient(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        server = context.makeTCPServer(WebSocketServerProtocol, WebSocketServerFactory())
        hook(WebSocketServerProtocol, 'onMessage', decoder=lambda payload, _: payload)
        client = yield context.makeTCPClient(
            MyClientProtocol, server, WebSocketClientFactory(), when='onOpen'
        )
        self.server = client.serverProtocol
        self.addCleanup(context.cleanup)

    @inlineCallbacks
    def testConnectDisconnect(self):
        yield self.server.onMessage.called()
        # cancel the loop:
        cancelDelayedCalls()

    @inlineCallbacks
    def testDisconnectDuringTest(self):
        self.server.transport.loseConnection()
        yield self.server.connectionLost.called()
        # cancel the loop:
        cancelDelayedCalls()

    @inlineCallbacks
    def testOneMessage(self):
        payload = yield self.server.onMessage.called()
        compare(payload, expected='tick 1')
        # cancel the loop:
        cancelDelayedCalls()

    @inlineCallbacks
    def testTwoMessages(self):
        compare((yield self.server.onMessage.called()), expected='tick 1')
        # advance time until after the loop will have fired:
        advanceTime(seconds=1.1)
        compare((yield self.server.onMessage.called()), expected='tick 2')
        # cancel the loop:
        cancelDelayedCalls()
