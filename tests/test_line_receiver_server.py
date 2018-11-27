from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import Context, decoder
from carly.tcp import makeTCPServer, makeTCPClient
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
        self.connection = client.connection
        self.addCleanup(context.cleanup)

    def testConnectDisconnect(self):
        pass

    @inlineCallbacks
    def testDisconnectDuringTest(self):
        self.connection.disconnect()
        yield self.client.connectionLost.called()

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
        line = yield self.client.lineReceived.called()
        compare(line, expected='goodbye')

    @inlineCallbacks
    def testSendTwoMessagesReceveBoth(self):
        self.client.sendLine('hello')
        self.client.sendLine('goodbye')
        line = yield self.client.lineReceived.called()
        compare(line, expected='hello')
        line = yield self.client.lineReceived.called()
        compare(line, expected='goodbye')
