from autobahn.twisted import (
    WebSocketClientProtocol, WebSocketClientFactory
)
from testfixtures import compare, TempDirectory
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, gatherResults
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.trial.unittest import TestCase
from twisted.web.client import Agent, readBody

from carly import Context, decoder, advanceTime, hook
from carly.tcp import TCPClient, makeTCPServer, makeTCPClient, waitForClient
from carly.websocket import makeWebSocketClient
from tests.web_site import buildSite, ServerProtocol


class ServerTester(WebSocketClientProtocol):

    def onConnect(self, response):
        self.factory.resetDelay()

    @decoder
    def onMessage(self, payload, isBinary):
        return payload

    def close(self):
        self.factory.stopTrying()
        self.sendClose()


class ServerTesterFactory(WebSocketClientFactory, ReconnectingClientFactory):

    protocol = ServerTester
    initialDelay = 0.01


class TestWebSocketServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = self.context = Context()
        self.dir = TempDirectory()
        self.addCleanup(self.dir.cleanup)
        # make sure that we trap unexpected close messages:
        hook(ServerProtocol, 'sendClose')
        self.server = makeTCPServer(
            context, ServerProtocol, buildSite(b'gotit', self.dir.path), installProtocol=False
        )
        client = yield makeWebSocketClient(
            context, self.server, factoryClass=ServerTesterFactory, close='close', endpoint='/spam'
        )
        self.client = client.clientProtocol
        self.addCleanup(context.cleanup, threads=True, delayedCalls=1)

    def testConnectDisconnect(self):
        pass

    @inlineCallbacks
    def testSendMessage(self):
        self.client.sendMessage(b'hello')
        message = yield self.client.onMessage.called()
        compare(message, expected=b'gotit')

    @inlineCallbacks
    def testSendBinary(self):
        self.client.sendMessage(b'hello', isBinary=True)
        yield ServerProtocol.sendClose.called()
        yield self.client.connectionLost.called()


    @inlineCallbacks
    def testPing(self):
        yield advanceTime(seconds=2.1)
        payload = yield self.client.onMessage.called(timeout=0.3)
        compare(payload, expected=b'ping 1')

    @inlineCallbacks
    def testReconnect(self):
        hook(ServerTester, 'onOpen')
        self.client.sendMessage(b'hello', isBinary=True)
        yield ServerProtocol.sendClose.called()
        yield self.client.connectionLost.called()

        client = yield waitForClient(
            self.context, ServerTester.onOpen, ServerProtocol.connectionMade, 'close'
        )
        server = client.serverProtocol
        client = client.clientProtocol

        client.sendMessage(b'hello')
        payload = yield client.onMessage.called()
        compare(payload, expected=b'gotit')

        # autobahn just doesn't use client protocol instances that aren't open, so
        # we manually check we're stripped out closed connections:
        compare(server.factory.state.clients, expected={server})

        yield advanceTime(seconds=2.1)
        
        payload = yield client.onMessage.called()
        compare(payload, expected=b'ping 1')

    def request(self, uri):
        agent = Agent(reactor)
        return agent.request(b'GET', u'http://{}:{}{}'.format(
            self.server.targetHost, self.server.targetPort, uri
        ).encode('ascii'))

    @inlineCallbacks
    def testWeb404(self):
        response = yield self.request('/test.html')
        compare(response.code, expected=404)

    @inlineCallbacks
    def testWeb200(self):
        self.dir.write('test.html', b'<html/>')
        response = yield self.request('/test.html')
        compare(response.code, expected=200)
        body = yield readBody(response)
        compare(body, expected=b'<html/>')
