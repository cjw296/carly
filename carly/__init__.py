from __future__ import print_function

from twisted.internet import reactor
from twisted.internet.defer import gatherResults

from .hook import hook

def waitUntilAll(*deferreds):
    for d in deferreds:
        # This short timeout is important so that if something goes wrong, we find
        # out about it soon, rather than blocking forever on something that can
        # can no longer happen.
        d.addTimeout(0.2, reactor)
    return gatherResults(deferreds)
