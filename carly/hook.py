from __future__ import print_function

from functools import partial

from collections import namedtuple

from twisted.internet.defer import Deferred
from twisted.internet import reactor

from types import ClassType

from .timeout import resolveTimeout

Result = namedtuple('Result', ['protocol', 'args', 'kw', 'result'])


class HookState(object):

    def __init__(self, once):
        self.once = once
        self.classDeferred = Deferred()
        self.instanceDeferreds = {}

    def resetDeferredFor(self, instance):
        self.classDeferred = Deferred()
        key = id(instance)
        if key in self.instanceDeferreds:
            del self.instanceDeferreds[key]

    def deferredFor(self, instance):
        if instance is None:
            return self.classDeferred
        key = id(instance)
        if key not in self.instanceDeferreds:
            self.instanceDeferreds[key] = Deferred()
        return self.instanceDeferreds[key]

    def handleCall(self, result):
        instance = result.protocol
        deferreds = self.deferredFor(None), self.deferredFor(instance)
        if not self.once:
            self.resetDeferredFor(instance)
        for d in deferreds:
            d.callback(result)

    def expectCallback(self, instance, handler, timeout):
        timeout = resolveTimeout(timeout)
        deferred = self.deferredFor(instance)
        return deferred.addTimeout(timeout, reactor).addCallback(handler)


class BoundHook(object):

    def __init__(self, state, original, instance, decoder):
        self.state = state
        self.original = original
        self.instance = instance
        self.decoder = decoder

    def __call__(self, *args, **kw):
        result = self.original(self.instance, *args, **kw)
        self.state.handleCall(Result(self.instance, args, kw, result))
        return result

    def _decode(self, decoder, result):
        decoder = decoder or self.decoder
        if decoder is None:
            return result
        return decoder(*result.args, **result.kw)

    def called(self, decoder=None, timeout=None):
        return self.state.expectCallback(self.instance, partial(self._decode, decoder), timeout)


class HookedCall(object):

    def __init__(self, class_, name, decoder=None, once=False):
        self.state = HookState(once)
        self.original = getattr(class_, name)
        self.decoder = decoder
        self.once = once

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundHook(self.state, self.original, instance, self.decoder)

    def protocol(self, timeout=None):
        return self.state.expectCallback(None, lambda result: result.protocol, timeout)


def hook(class_, initial):
    """
    Create a subclass that can have its methods hooked so the instance calls can
    be used to fire deferreds used in testing.

    :param initial:
      The method to hook in order to pick up the instance of the class being hooked.
    """
    attrs = {'__carly_hooked__': True}
    attrs[initial] = HookedCall(class_, initial)

    if issubclass(class_, object):
        type_ = type
    else:
        # some protocols don't have object has a base class!
        type_ = ClassType

    return type_('Hooked'+class_.__name__, (class_,), attrs)


def hookMethod(class_, name, decoder=None, once=False):
    """
    Hook a method on a hooked class such that tests can wait on it being called
    on a particular instance.

    :param name:
      The name of the method to hook.

    :param decoder:
      A callable that will be used to decode the result of the method being called.
      It should take the same arguments and parameters as the method being hooked and should
      return whatever is required by the test that is going to wait on calls to this method.

    :param once:
      Only expect one call on this method. Multiple waits in a test will all end up
      waiting on the same call. This is most useful when hooking connections going away,
      where the test may want to explicitly wait for this, while the tear down of the test
      will also need to wait on it.
    """
    if not getattr(class_, '__carly_hooked__', False):
        raise AssertionError("Can't hook a method on an unhooked class")
    setattr(class_, name, HookedCall(class_, name, decoder, once))
