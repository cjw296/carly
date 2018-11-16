from __future__ import print_function

from collections import namedtuple

from twisted.internet.defer import Deferred
from twisted.internet import reactor

from types import ClassType


DEFAULT_TIMEOUT = 0.2

Result = namedtuple('Result', ['protocol', 'args', 'kw'])


class BoundHook(object):

    def __init__(self, hooked, original, instance):
        self.hooked = hooked
        self.original = original
        self.instance = instance

    def __call__(self, *args, **kw):
        result = self.original(self.instance, *args, **kw)
        self.hooked._called.callback(Result(self.instance, args, kw))
        return result


class HookedCall(object):

    def __init__(self, class_, hook):
        self._called = Deferred()
        self.original = getattr(class_, hook)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundHook(self, self.original, instance)

    def called(self, timeout=DEFAULT_TIMEOUT):
        return self._called.addTimeout(timeout, reactor).addCallback(
            lambda result: None
        )

    def protocol(self, timeout=DEFAULT_TIMEOUT):
        return self._called.addTimeout(timeout, reactor).addCallback(
            lambda result: result.protocol
        )


def hook(class_, *hooks):
    methods = {}
    for hook in hooks:
        d = Deferred()
        methods[hook] = HookedCall(class_, hook)

    if issubclass(class_, object):
        type_ = type
    else:  # pragma: no cover
        # some protocols don't have object has a base class!
        type_ = ClassType

    return type_('Hooked'+class_.__name__, (class_,), methods)
