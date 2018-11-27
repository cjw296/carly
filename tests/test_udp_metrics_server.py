from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from carly import Context
from carly.udp import makeUDP
from .udp_metrics import CollectorProtocol


class TestUDPCollector(TestCase):

    def setUp(self):
        context = Context()
        self.collector = CollectorProtocol()
        self.udp = makeUDP(context, self.collector)
        self.addCleanup(context.cleanup)

    def testDoNothing(self):
        pass

    @inlineCallbacks
    def testOneClient(self):
        self.udp.send('{"id": "a"}')
        self.udp.send('{"id": "a"}')
        yield self.collector.datagramReceived.called()
        compare(self.collector.counts, expected={'a': 1})
        yield self.collector.datagramReceived.called()
        compare(self.collector.counts, expected={'a': 2})

    @inlineCallbacks
    def testMultipleClient(self):
        self.udp.send('{"id": "a"}')
        self.udp.send('{"id": "b"}')
        yield self.collector.datagramReceived.called()
        yield self.collector.datagramReceived.called()
        compare(self.collector.counts, expected={'a': 1, 'b': 1})
