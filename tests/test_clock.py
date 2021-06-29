from testfixtures import ShouldRaise, compare, Replace, not_there
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.trial.unittest import TestCase

from carly import cancelDelayedCalls, advanceTime
from carly.clock import withTimeout


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


class MockDeferred(object):

    def addTimeout(self, timeout, _):
        self.timeout = timeout
        return self


class TestWithTimeout(TestCase):

    def testNormal(self):
        with Replace('os.environ.CARLY_MINIMUM_TIMEOUT', not_there, strict=False):
            actual = withTimeout(MockDeferred())
        compare(actual.timeout, expected=0.2)

    def testExplicit(self):
        with Replace('os.environ.CARLY_MINIMUM_TIMEOUT', not_there, strict=False):
            actual = withTimeout(MockDeferred(), timeout=42)
        compare(actual.timeout, expected=42)

    def testFromEnv(self):
        with Replace('os.environ.CARLY_MINIMUM_TIMEOUT', '42', strict=False):
            actual = withTimeout(MockDeferred())
        compare(actual.timeout, expected=42)

    def testExplicitLongerThanEnv(self):
        with Replace('os.environ.CARLY_MINIMUM_TIMEOUT', '1', strict=False):
            actual = withTimeout(MockDeferred(), timeout=2)
        compare(actual.timeout, expected=2)

    def testEnvLongerThanExplicit(self):
        with Replace('os.environ.CARLY_MINIMUM_TIMEOUT', '2', strict=False):
            actual = withTimeout(MockDeferred(), timeout=1)
        compare(actual.timeout, expected=2)
