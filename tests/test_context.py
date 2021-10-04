from twisted.trial.unittest import TestCase

from carly import Context


class TestContext(TestCase):

    def testMultipleCleanupCalls(self):
        context = Context()
        context.cleanup()
        context.cleanup()
