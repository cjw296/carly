from __future__ import print_function

from functools import partial

from collections import namedtuple

from twisted.internet.defer import Deferred
from twisted.internet import reactor

from types import ClassType

from .timeout import resolveTimeout

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

    def __getattr__(self, item):
        return getattr(self.hooked, item)


class HookedCall(object):

    def __init__(self, class_, hook, decoder=None, once=False):
        self._called = Deferred()
        self.original = getattr(class_, hook)
        self.decoder = decoder
        self.once = once

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundHook(self, self.original, instance)

    def _reset(self, handler, timeout, result):
        if isinstance(result, Result):
            return handler(result)
        else:
            self._called = Deferred()
            self._called.addTimeout(timeout, reactor).addCallback(handler)
            return self._called

    def _once(self, handler, result):
        if result is not None:
            return handler(result)

    def _expectCallback(self, handler, timeout):
        timeout = resolveTimeout(timeout)
        if self.once:
            callback = partial(self._once, handler)
        else:
            callback = partial(self._reset, handler, timeout)
        return self._called.addTimeout(timeout, reactor).addCallback(callback)

    def _decode(self, decoder, result):
        decoder = decoder or self.decoder
        if decoder is None:
            return result
        return decoder(*result.args, **result.kw)

    def called(self, decoder=None, timeout=None):
        return self._expectCallback(partial(self._decode, decoder), timeout)

    def protocol(self, timeout=None):
        return self._expectCallback(lambda result: result.protocol, timeout)


def hook(class_, *names):
    methods = {'__carly_hooked__': True}
    for name in names:
        d = Deferred()
        methods[name] = HookedCall(class_, name)

    if issubclass(class_, object):
        type_ = type
    else:  # pragma: no cover
        # some protocols don't have object has a base class!
        type_ = ClassType

    return type_('Hooked'+class_.__name__, (class_,), methods)


def hookMethod(class_, name, decoder=None, once=False):
    if not getattr(class_, '__carly_hooked__', False):
        raise AssertionError("Can't hook a method on an unhooked class")
    setattr(class_, name, HookedCall(class_, name, decoder, once))
