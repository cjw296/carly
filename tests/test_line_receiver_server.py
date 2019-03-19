from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import Context, decoder
from carly.tcp import makeTCPServer, makeTCPClient, disconnect
from .line_receiver import EchoServer


class ClientProtocol(LineReceiver):

    @decoder
    def lineReceived(self, line):
        return line


class TestLineReceiverServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        server = makeTCPServer(context, EchoServer)
        client = yield makeTCPClient(context, ClientProtocol, server)
        self.client = client.clientProtocol
        self.addCleanup(context.cleanup)

    def testConnectDisconnect(self):
        pass

    @inlineCallbacks
    def testDisconnectDuringTest(self):
        self.client.transport.loseConnection()
        yield self.client.connectionLost.called()

    @inlineCallbacks
    def testOneMessage(self):
        self.client.sendLine(b'hello')
        line = yield self.client.lineReceived.called()
        compare(line, expected=b'hello')

    @inlineCallbacks
    def testSendMessageReceiveMessageSendMessageRecieveMessage(self):
        self.client.sendLine(b'hello')
        line = yield self.client.lineReceived.called()
        compare(line, expected=b'hello')
        self.client.sendLine(b'goodbye')
        line = yield self.client.lineReceived.called()
        compare(line, expected=b'goodbye')

    @inlineCallbacks
    def testSendTwoMessagesReceveBoth(self):
        self.client.sendLine(b'hello')
        self.client.sendLine(b'goodbye')
        line = yield self.client.lineReceived.called()
        compare(line, expected=b'hello')
        line = yield self.client.lineReceived.called()
        compare(line, expected=b'goodbye')
