from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol
from twisted.trial.unittest import TestCase

from carly import Context, hook, decoder
from .line_receiver import EchoClient


class ServerProtocol(Protocol):

    @decoder
    def dataReceived(self, data):
        return data


class TestLineReceiverClient(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        server = context.makeTCPServer(ServerProtocol)
        client = yield context.makeTCPClient(EchoClient, server)
        hook(EchoClient, 'lineReceived')
        self.client = client.clientProtocol
        self.server = client.serverProtocol
        self.addCleanup(context.cleanup)

    @inlineCallbacks
    def testConnectDisconnect(self):
        yield self.server.dataReceived.called()

    @inlineCallbacks
    def testServerDisconnectsDuringTest(self):
        yield self.server.dataReceived.called()
        self.server.transport.loseConnection()
        yield self.server.connectionLost.called()

    @inlineCallbacks
    def testClientDisconnectsDuringTest(self):
        self.server.transport.write(EchoClient.end+EchoClient.delimiter)
        yield self.client.lineReceived.called()
        yield self.server.connectionLost.called()
        yield self.server.dataReceived.called()

    @inlineCallbacks
    def testMessages(self):
        data = yield self.server.dataReceived.called()
        compare(data, expected=(
            b'Hello, world!\r\n'
            b'Bye-bye!\r\n'
        ))
