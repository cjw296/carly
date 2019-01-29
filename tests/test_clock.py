from testfixtures import ShouldRaise
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from carly import cancelDelayedCalls, advanceTime


def call1(x): pass

def call2(y): pass


class TestCancelDelayedCall(TestCase):

    def testWrongNumber(self):
        reactor.callLater(5, call1, 42)
        reactor.callLater(10, call1, 13)
        with ShouldRaise(AssertionError) as s:
            cancelDelayedCalls(expected=1)
        actual = str(s.raised)
        assert actual.startswith('\n\nExpected 1 delayed calls, found 2: ['), actual
        assert 'call1(42)>' in actual
        assert 'call1(13)>' in actual


def fire(called):
    called.append(True)


def fireLater(called):
    reactor.callLater(5, fire, called)


class TestAdvanceTime(TestCase):

    @inlineCallbacks
    def testLetDeferredsScheduleTheirCalls(self):
        called = []
        reactor.callLater(0, fireLater, called)
        yield advanceTime(seconds=6)
        assert called
