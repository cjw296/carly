from __future__ import print_function

from functools import partial

from collections import namedtuple, defaultdict

from twisted.internet.defer import Deferred, inlineCallbacks, succeed, returnValue
from twisted.internet import reactor

from types import ClassType

from .timeout import resolveTimeout

Result = namedtuple('Result', ['protocol', 'args', 'kw', 'result'])


class HookState(object):

    def __init__(self, once):
        self.once = once
        self.instanceDeferreds = defaultdict(Deferred)
        self.instanceQueues = defaultdict(list)

    def handleCall(self, result):
        instance = result.protocol
        for target in None, instance:
            self.instanceQueues[target].append(result)
            deferred = self.instanceDeferreds[target]
            if target is None or not self.once:
                del self.instanceDeferreds[target]
            deferred.callback(result)

    @inlineCallbacks
    def expectCallback(self, instance, timeout):
        queue = self.instanceQueues[instance]
        if not queue:
            deferred = self.instanceDeferreds[instance]
            timeout = resolveTimeout(timeout)
            yield deferred.addTimeout(timeout, reactor)
        if self.once:
            returnValue(queue[0])
        else:
            returnValue(queue.pop(0))


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

    @inlineCallbacks
    def called(self, decoder=None, timeout=None):
        result = yield self.state.expectCallback(self.instance, timeout)
        decoder = decoder or self.decoder
        if decoder is None:
            returnValue(result)
        returnValue(decoder(*result.args, **result.kw))


class HookedCall(object):

    def __init__(self, class_, original, decoder=None, once=False):
        self.state = HookState(once)
        self.original = original
        self.decoder = decoder
        self.once = once

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundHook(self.state, self.original, instance, self.decoder)

    @inlineCallbacks
    def protocol(self, timeout=None):
        result = yield self.state.expectCallback(None, timeout)
        returnValue(result.protocol)


class Hooked: pass


def hookClass(class_):
    """
    Create a subclass that can have its methods hooked so the instance calls can
    be used to fire deferreds used in testing.
    """
    if not issubclass(class_, Hooked):
        if issubclass(class_, object):
            type_ = type
        else:
            # some protocols don't have object has a base class!
            type_ = ClassType
        class_ = type_('Hooked'+class_.__name__, (Hooked, class_), {})
    return class_


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
    if not issubclass(class_, Hooked):
        raise AssertionError("Can't hook a method on an unhooked class")
    original = getattr(class_, name)
    if not isinstance(original, HookedCall):
        setattr(class_, name, HookedCall(class_, original, decoder, once))
