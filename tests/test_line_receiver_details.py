from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import Context, hook, decoder
from carly.tcp import makeTCPServer, makeTCPClient
from .line_receiver import EchoServer


class ClientProtocol(LineReceiver):

    @decoder
    def lineReceived(self, line):
        return line


class TestAllInMethod(TestCase):

    @inlineCallbacks
    def testConnectDisconnect(self):
        context = Context()
        server = makeTCPServer(context, EchoServer)
        client = yield makeTCPClient(context, ClientProtocol, server)
        self.client = client.clientProtocol
        yield context.cleanup()


    @inlineCallbacks
    def testNoClient(self):
        context = Context()
        makeTCPServer(context, EchoServer)
        yield context.cleanup()


class TestDetails(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        server = makeTCPServer(context, EchoServer)
        client = yield makeTCPClient(context, ClientProtocol, server)
        self.client = client.clientProtocol
        self.addCleanup(context.cleanup)

    @inlineCallbacks
    def testSpecificDecoder(self):
        self.client.sendLine('hello')
        line = yield self.client.lineReceived.called(lambda line: line+'!')
        compare(line, expected='hello!')
