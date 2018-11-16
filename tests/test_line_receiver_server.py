from testfixtures import compare
from twisted.internet import protocol, reactor
from twisted.internet.defer import inlineCallbacks, maybeDeferred
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import hook, waitUntilAll
from carly.hook import hookMethod

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
        hookMethod(self.clientProtocolClass, 'lineReceived', decoder=lambda line: line)
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

    @inlineCallbacks
    def testOneMessage(self):
        self.client.sendLine('hello')
        line = yield self.client.lineReceived.called()
        compare(line, expected='hello')

    @inlineCallbacks
    def testSendMessageReceiveMessageSendMessageRecieveMessage(self):
        self.client.sendLine('hello')
        line = yield self.client.lineReceived.called()
        compare(line, expected='hello')
        self.client.sendLine('goodbye')
        # also test explicit decoder:
        line = yield self.client.lineReceived.called(lambda line: line+'!')
        compare(line, expected='goodbye!')

    @inlineCallbacks
    def testSendTwoMessagesReceveBoth(self):
        self.client.sendLine('hello')
        line = yield self.client.lineReceived.called()
        compare(line, expected='hello')
        self.client.sendLine('goodbye')
        line = yield self.client.lineReceived.called()
        compare(line, expected='goodbye')
