from __future__ import print_function

from pprint import pformat

from attr import attrs, attrib
from collections import namedtuple, defaultdict
from twisted.internet import reactor
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue

from .timeout import resolveTimeout

@attrs(slots=True)
class Result(object):
    protocol = attrib(repr=False)
    args = attrib()
    kw = attrib()
    result = attrib(repr=False)
    consumed = attrib(repr=False, default=False)


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
            result = queue[0]
        else:
            result = queue.pop(0)
        result.consumed = True
        returnValue(result)

    def cleanup(self):
        allUnconsumed = {}
        for instance, queue in self.instanceQueues.items():
            unconsumed = tuple(r for r in queue if not r.consumed)
            if unconsumed:
                allUnconsumed[instance] = unconsumed
            queue[:] = []
        return allUnconsumed


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


class UnconsumedCalls(AssertionError):

    def __init__(self, unconsumed):
        self.unconsumed = unconsumed

    def __str__(self):
        return pformat(self.unconsumed)


class HookedCall(object):

    all = {}

    def __init__(self, class_, name, decoder=None, once=False):
        self.original = getattr(class_, name)
        self.class_ = class_
        self.name = name
        self.state = HookState(once)
        self.decoder = decoder
        self.once = once
        setattr(class_, name, self)
        self.all[class_, name] = self

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return BoundHook(self.state, self.original, instance, self.decoder)

    @inlineCallbacks
    def protocol(self, timeout=None):
        result = yield self.state.expectCallback(None, timeout)
        returnValue(result.protocol)

    @classmethod
    def cleanup(cls):
        allUnconsumed = {}
        for key, hook in cls.all.items():
            setattr(hook.class_, hook.name, hook.original)
            unconsumed = hook.state.cleanup()
            if unconsumed:
                allUnconsumed[key] = unconsumed
        if allUnconsumed:
            raise UnconsumedCalls(allUnconsumed)


def hook(class_, name, decoder=None, once=False):
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
    method = getattr(class_, name)
    if not isinstance(method, HookedCall):
        method = HookedCall(class_, name, decoder, once)
    return method


cleanup = HookedCall.cleanup
