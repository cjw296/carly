from testfixtures import compare, Replacer
from twisted.internet.defer import inlineCallbacks, gatherResults
from twisted.protocols.basic import LineReceiver
from twisted.trial.unittest import TestCase

from carly import Context,  hookMethod, hookClass
from .chat_server import ChatFactory, Chat


class ClientProtocol(LineReceiver):

    delimiter = b'\n'

    def lineReceived(self, line): pass


class TestChatServer(TestCase):

    @inlineCallbacks
    def setUp(self):
        context = Context()


        Chat_ = hookClass(Chat)
        r = Replacer()
        r.replace('tests.chat_server.Chat', Chat_)
        self.addCleanup(r.restore)

        self.factory = ChatFactory()
        server = context.makeTCPServer(Chat_, self.factory)

        protocolClass = hookClass(ClientProtocol)
        hookMethod(protocolClass, 'lineReceived', lambda line: line)
        self.client1 = (yield context.makeTCPClient(protocolClass, server)).clientProtocol
        self.client2 = (yield context.makeTCPClient(protocolClass, server)).clientProtocol
        self.addCleanup(context.cleanup)

    @inlineCallbacks
    def testLogin(self):
        compare((yield self.client1.lineReceived.called()),
                expected="What's your name?")
        self.client1.sendLine('chris')
        compare((yield self.client1.lineReceived.called()),
                expected="Welcome, chris!")

    @inlineCallbacks
    def testNameAlreadyTaken(self):
        self.client1.sendLine('dave')
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
