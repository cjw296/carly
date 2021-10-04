from testfixtures.mock import Mock
from twisted.trial.unittest import TestCase

from carly import Once


class TestOnce(TestCase):

    def testSimple(self):
        mock = Mock()
        wrapped = Once(mock)
        wrapped(1, two=3)
        wrapped(4, five=6)
        mock.assert_called_once_with(1, two=3)
