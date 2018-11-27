import json

from testfixtures import compare
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import DatagramProtocol
from twisted.trial.unittest import TestCase

from carly import Context, decoder, cancelDelayedCalls, advanceTime
from carly.udp import makeUDP
from .udp_metrics import SenderProtocol

class Receiver(DatagramProtocol):

    @decoder
    def datagramReceived(self, data, addr):
        return json.loads(data)


class TestLineReceiverServer(TestCase):

    def setUp(self):
        context = Context()
        self.receiver = Receiver()
        udp = makeUDP(context, self.receiver)
        self.sender = SenderProtocol(udp.targetHost, udp.targetPort)
        makeUDP(context, self.sender)
        self.addCleanup(context.cleanup)
        # stop the client loop:
        self.addCleanup(cancelDelayedCalls, expected=1)

    def testDoNothing(self):
        pass

    @inlineCallbacks
    def testOnePing(self):
        expectedId = 'client'+str(id(self.sender))
        data = yield self.receiver.datagramReceived.called()
        compare(data, expected={'id': expectedId})

    @inlineCallbacks
    def testTwoPings(self):
        expectedId = 'client'+str(id(self.sender))
        data = yield self.receiver.datagramReceived.called()
        compare(data, expected={'id': expectedId})
        yield advanceTime(seconds=1.1)
        data = yield self.receiver.datagramReceived.called()
        compare(data, expected={'id': expectedId})
