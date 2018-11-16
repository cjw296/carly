from twisted.internet import protocol, reactor
from twisted.internet.defer import inlineCallbacks, maybeDeferred
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import hook, waitUntilAll

from .line_receiver import EchoServer


class ClientProtocol(LineReceiver):
    def lineReceived(self, line): pass


class TestLineReceiverServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        self.serverProtocolClass = hook(EchoServer, 'connectionLost')
        f = protocol.Factory()
        f.protocol = self.serverProtocolClass
        self.serverPort = reactor.listenTCP(0, f)
        self.clientProtocolClass = hook(ClientProtocol, 'connectionMade', 'connectionLost')
        factory = protocol.ClientFactory()
        factory.protocol = self.clientProtocolClass
        self.clientConnection = reactor.connectTCP('localhost', self.serverPort.getHost().port, factory)
        self.client = yield self.clientProtocolClass.connectionMade.protocol()

    @inlineCallbacks
    def tearDown(self):
        yield waitUntilAll(
            maybeDeferred(self.clientConnection.disconnect),
            self.clientProtocolClass.connectionLost.called(),
            self.serverProtocolClass.connectionLost.called(),
        )
        yield waitUntilAll(
            maybeDeferred(self.serverPort.stopListening),
        )

    def testConnectDisconnect(self):
        pass
