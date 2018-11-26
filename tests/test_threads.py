from time import sleep

from testfixtures import compare, ShouldRaise
from twisted.internet.defer import inlineCallbacks, TimeoutError
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.trial.unittest import TestCase

from carly import advanceTime, cancelDelayedCalls, waitForThreads


def setState(state, duration):
    sleep(duration)
    state.fired += 1


def work(state, duration):
    deferToThread(setState, state, duration)


class TestDeferToThread(TestCase):

    fired = 0

    @inlineCallbacks
    def testWorkOne(self):
        LoopingCall(work, self, 0.001).start(2)
        advanceTime(seconds=0.2)
        yield waitForThreads()
        compare(self.fired, expected=1)
        cancelDelayedCalls()

    @inlineCallbacks
    def testWorkTwo(self):
        LoopingCall(work, self, 0.001).start(2)
        advanceTime(seconds=0.2)
        yield waitForThreads()
        compare(self.fired, expected=1)
        cancelDelayedCalls()

    @inlineCallbacks
    def testTimeout(self):
        LoopingCall(work, self, duration=0.1).start(2)
        with ShouldRaise(TimeoutError(0.02, 'Deferred')):
            yield waitForThreads(timeout=0.02)
        cancelDelayedCalls()
