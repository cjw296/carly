from testfixtures import ShouldRaise
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, Deferred
from twisted.trial.unittest import TestCase

from carly import hook


class PITA(object):

    def synchronousMethod(self, p):
        self.asyncMethod(p)

    @inlineCallbacks
    def asyncMethod(self, param):
        for i in range(5):
            yield self.asyncYielder(param, i)

    @inlineCallbacks
    def asyncYielder(self, param, i):
        if i == param:
            raise Exception(i)
        yield


class TestPITA(TestCase):

    @inlineCallbacks
    def test1(self):
        hook(PITA, 'asyncMethod')
        pita = PITA()
        pita.synchronousMethod(1)
        call = yield pita.asyncMethod.called()
        with ShouldRaise(Exception(1)):
            yield call.result
