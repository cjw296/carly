from testfixtures import ShouldRaise, compare
from twisted.internet.defer import inlineCallbacks, TimeoutError
from twisted.trial.unittest import TestCase

from carly import hook, cleanup
from carly.hook import UnconsumedCalls, Call


class Sample(object):

    def method(self, foo):
        return 'foo'


class TestHook(TestCase):

    def testUnconsumedCalls(self):
        hook(Sample, 'method')
        obj = Sample()
        obj.method('foo')
        with ShouldRaise(UnconsumedCalls({
            (Sample, 'method'): {obj: (Call(protocol=obj,
                                            args=('foo',),
                                            kw={},
                                            result='foo'),)}
        })):
            cleanup()

    def testUnconsumedstr(self):
        compare(str(UnconsumedCalls({})), expected='\n{}')

    @inlineCallbacks
    def testMultipleExpectedBeforeCalls(self):
        hook(Sample, 'method')
        self.addCleanup(cleanup)
        obj = Sample()
        call1 = obj.method.called()
        call2 = obj.method.called()
        obj.method('foo')
        obj.method('foo')
        yield call2
        yield call1

    @inlineCallbacks
    def testTimeout(self):
        hook(Sample, 'method')
        self.addCleanup(cleanup)
        obj = Sample()
        with ShouldRaise(TimeoutError):
            yield obj.method.called(timeout=0.01)
