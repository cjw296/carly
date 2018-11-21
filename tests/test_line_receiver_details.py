from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import Context, hook
from .line_receiver import EchoServer


class ClientProtocol(LineReceiver):
    def lineReceived(self, line): pass


class TestAllInMethod(TestCase):

    @inlineCallbacks
    def testConnectDisconnect(self):
        context = Context()
        server = context.makeTCPServer(EchoServer)
        client = yield context.makeTCPClient(ClientProtocol, server)
        hook(client.protocolClass, 'lineReceived', decoder=lambda line: line)
        self.client = client.clientProtocol
        self.connection = client.connection
        yield context.cleanup()


    @inlineCallbacks
    def testNoClient(self):
        context = Context()
        context.makeTCPServer(EchoServer)
        yield context.cleanup()


class TestDetails(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        server = context.makeTCPServer(EchoServer)
        client = yield context.makeTCPClient(ClientProtocol, server)
        hook(client.protocolClass, 'lineReceived', decoder=lambda line: line)
        self.client = client.clientProtocol
        self.connection = client.connection
        self.addCleanup(context.cleanup)

    @inlineCallbacks
    def testSpecificDecoder(self):
        self.client.sendLine('hello')
        line = yield self.client.lineReceived.called(lambda line: line+'!')
        compare(line, expected='hello!')
