from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import Context, advanceTime, decoder
from carly.tcp import makeTCPClient, makeTCPServer
from .chat_server import ChatFactory, Chat


class ClientProtocol(LineReceiver):

    delimiter = b'\n'

    @decoder
    def lineReceived(self, line):
        return line


class TestChatServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()
        self.factory = ChatFactory()
        server = makeTCPServer(context, Chat, self.factory, installProtocol=False)
        self.client1 = (yield makeTCPClient(context, ClientProtocol, server)).clientProtocol
        self.client2 = (yield makeTCPClient(context, ClientProtocol, server)).clientProtocol
        self.addCleanup(context.cleanup)

    @inlineCallbacks
    def testLogin(self):
        compare((yield self.client1.lineReceived.called()),
                expected=b"What's your name?")
        self.client1.sendLine(b'chris')
        compare((yield self.client1.lineReceived.called()),
                expected=b"Welcome, chris!")
        # consume the client 2 greeting:
        yield self.client2.lineReceived.called()


    @inlineCallbacks
    def testNameAlreadyTaken(self):
        yield self.client1.lineReceived.called()
        self.client1.sendLine(b'dave')
        yield self.client1.lineReceived.called()

        compare((yield self.client2.lineReceived.called()),
                expected=b"What's your name?")
        self.client2.sendLine(b'dave')
        compare((yield self.client2.lineReceived.called()),
                expected=b"Name taken, please choose another.")

    @inlineCallbacks
    def loginClients(self):
        # greetings
        yield self.client1.lineReceived.called()
        yield self.client2.lineReceived.called()
        # pick name
        self.client1.sendLine(b'dave')
        self.client2.sendLine(b'chris')
        # login
        yield self.client1.lineReceived.called()
        yield self.client2.lineReceived.called()

    @inlineCallbacks
    def testChat(self):
        yield self.loginClients()
        self.client1.sendLine(b'Hi!')
        result = yield self.client2.lineReceived.called()
        compare(result, expected=b'<dave> Hi!')

    @inlineCallbacks
    def testTick(self):
        yield self.loginClients()
        self.factory.start()
        yield advanceTime(seconds=1.1)
        compare((yield self.client1.lineReceived.called()),
                expected=b"<tick> 0")
        compare((yield self.client2.lineReceived.called()),
                expected=b"<tick> 0")
        yield advanceTime(seconds=1.1)
        compare((yield self.client1.lineReceived.called()),
                expected=b"<tick> 1")
        compare((yield self.client2.lineReceived.called()),
                expected=b"<tick> 1")
        self.factory.stop()
