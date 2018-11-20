from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol
from twisted.trial.unittest import TestCase

from carly import Context, hookMethod
from .line_receiver import EchoClient


class ServerProtocol(Protocol): pass


class TestLineReceiverClient(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        server = context.makeTCPServer(ServerProtocol)
        hookMethod(server.protocolClass, 'dataReceived', decoder=lambda data: data)
        client = yield context.makeTCPClient(EchoClient, server)
        hookMethod(client.protocolClass, 'lineReceived')
        self.client = client.clientProtocol
        self.server = client.serverProtocol
        self.addCleanup(context.cleanup)

    def testConnectDisconnect(self):
        pass

    @inlineCallbacks
    def testServerDisconnectsDuringTest(self):
        self.server.transport.loseConnection()
        yield self.server.connectionLost.called()

    @inlineCallbacks
    def testClientDisconnectsDuringTest(self):
        self.server.transport.write(EchoClient.end+EchoClient.delimiter)
        yield self.client.lineReceived.called()
        yield self.server.connectionLost.called()

    @inlineCallbacks
    def testMessages(self):
        data = yield self.server.dataReceived.called()
        compare(data, expected=(
            b'Hello, world!\r\n'
            b'Bye-bye!\r\n'
        ))
