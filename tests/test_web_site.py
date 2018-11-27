from autobahn.twisted import (
    WebSocketClientProtocol, WebSocketClientFactory
)
from testfixtures import compare, TempDirectory
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.trial.unittest import TestCase
from twisted.web.client import Agent, readBody

from carly import Context, decoder, cancelDelayedCalls, advanceTime, waitForThreads, hook
from tests.web_site import buildSite, ServerProtocol


class ServerTester(WebSocketClientProtocol):

    @decoder
    def onMessage(self, payload, isBinary):
        return payload


class TestWebSocketServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = self.context = Context()
        self.dir = TempDirectory()
        self.addCleanup(self.dir.cleanup)
        self.server = context.makeTCPServer(ServerProtocol,
                                            buildSite('gotit', self.dir.path),
                                            installProtocol=False)
        factory = WebSocketClientFactory("ws://{}:{}/spam".format(
            self.server.targetHost, self.server.targetPort
        ))
        client = yield context.makeTCPClient(
            ServerTester, self.server, factory, when='onOpen'
        )
        # make sure that we trap unexpected close messages:
        hook(ServerProtocol, 'sendClose')
        self.client = client.clientProtocol
        self.addCleanup(context.cleanup, threads=True, delayedCalls=1)

    def testConnectDisconnect(self):
        pass

    @inlineCallbacks
    def testSendMessage(self):
        self.client.sendMessage(b'hello')
        message = yield self.client.onMessage.called()
        compare(message, expected='gotit')

    @inlineCallbacks
    def testSendBinary(self):
        self.client.sendMessage(b'hello', isBinary=True)
        yield ServerProtocol.sendClose.called()
        yield self.client.connectionLost.called()


    @inlineCallbacks
    def testPing(self):
        yield advanceTime(seconds=2.1)
        payload = yield self.client.onMessage.called(timeout=0.3)
        compare(payload, expected='ping 1')

    def request(self, uri):
        agent = Agent(reactor)
        return agent.request('GET', 'http://{}:{}{}'.format(
            self.server.targetHost, self.server.targetPort, uri
        ))

    @inlineCallbacks
    def testWeb404(self):
        response = yield self.request('/test.html')
        compare(response.code, expected=404)

    @inlineCallbacks
    def testWeb200(self):
        self.dir.write('test.html', '<html/>')
        response = yield self.request('/test.html')
        compare(response.code, expected=200)
        body = yield readBody(response)
        compare(body, expected='<html/>')
