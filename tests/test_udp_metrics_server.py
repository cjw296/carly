from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from carly import Context
from .udp_metrics import CollectorProtocol


class TestLineReceiverServer(TestCase):

    def setUp(self):
        context = Context()
        self.server = CollectorProtocol()
        self.udp = context.makeUDP(self.server)
        self.addCleanup(context.cleanup)

    def testDoNothing(self):
        pass

    @inlineCallbacks
    def testOneClient(self):
        self.udp.send('{"id": "a"}')
        self.udp.send('{"id": "a"}')
        yield self.server.datagramReceived.called()
        compare(self.server.counts, expected={'a': 1})
        yield self.server.datagramReceived.called()
        compare(self.server.counts, expected={'a': 2})

    @inlineCallbacks
    def testMultipleClient(self):
        self.udp.send('{"id": "a"}')
        self.udp.send('{"id": "b"}')
        yield self.server.datagramReceived.called()
        yield self.server.datagramReceived.called()
        compare(self.server.counts, expected={'a': 1, 'b': 1})
