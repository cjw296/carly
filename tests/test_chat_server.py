from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import Context, hook
from .chat_server import ChatFactory, Chat


class ClientProtocol(LineReceiver):

    delimiter = b'\n'

    def lineReceived(self, line): pass


class TestChatServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()

        self.factory = ChatFactory()
        server = context.makeTCPServer(Chat, self.factory)

        hook(ClientProtocol, 'lineReceived', lambda line: line)
        self.client1 = (yield context.makeTCPClient(ClientProtocol, server)).clientProtocol
        self.client2 = (yield context.makeTCPClient(ClientProtocol, server)).clientProtocol
        self.addCleanup(context.cleanup)

    @inlineCallbacks
    def testLogin(self):
        compare((yield self.client1.lineReceived.called()),
                expected="What's your name?")
        self.client1.sendLine('chris')
        compare((yield self.client1.lineReceived.called()),
                expected="Welcome, chris!")
        # consume the client 2 greeting:
        yield self.client2.lineReceived.called()


    @inlineCallbacks
    def testNameAlreadyTaken(self):
        yield self.client1.lineReceived.called()
        self.client1.sendLine('dave')
        yield self.client1.lineReceived.called()

        compare((yield self.client2.lineReceived.called()),
                expected="What's your name?")
        self.client2.sendLine('dave')
        compare((yield self.client2.lineReceived.called()),
                expected="Name taken, please choose another.")

    @inlineCallbacks
    def testChat(self):
        # greetings
        yield self.client1.lineReceived.called()
        yield self.client2.lineReceived.called()
        # pick name
        self.client1.sendLine('dave')
        self.client2.sendLine('chris')
        # login
        yield self.client1.lineReceived.called()
        yield self.client2.lineReceived.called()
        self.client1.sendLine('Hi!')
        result = yield self.client2.lineReceived.called()
        compare(result, expected='<dave> Hi!')
