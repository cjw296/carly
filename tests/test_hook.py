from testfixtures import ShouldRaise, compare
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
