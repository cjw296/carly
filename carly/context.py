from functools import partial

from collections import namedtuple

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, gatherResults, maybeDeferred
from twisted.internet.protocol import Factory, ClientFactory

from .hook import hook
from .timeout import resolveTimeout

TCPServer = namedtuple('TCPServer', ['protocolClass', 'port'])
TCPClient = namedtuple('TCPClient', ['protocolClass', 'connection', 'protocol'])


class Context(object):

    def __init__(self):
        self.cleanups = {
            'connections': [],
            'listens': [],
        }

    def _cleanup(self, cleanups, timeout):
        deferreds = []
        for p in cleanups:
            d = p()
            deferreds.append(d)
            d.addTimeout(timeout, reactor)
        return gatherResults(deferreds)

    @inlineCallbacks
    def cleanup(self, timeout=None):
        timeout = resolveTimeout(timeout)
        yield self._cleanup(self.cleanups['connections'], timeout)
        yield self._cleanup(self.cleanups['listens'], timeout)

    def makeTCPServer(self, protocol, factory=None):
        protocolClass = hook(protocol, 'connectionLost')
        if factory is None:
            factory = Factory()
        factory.protocol = protocolClass
        port = reactor.listenTCP(0, factory)
        server = TCPServer(protocolClass, port)
        self.cleanupTCPServer(server)
        return server

    def cleanupTCPServer(self, server, timeout=None):
        timeout = resolveTimeout(timeout)
        self.cleanups['connections'].append(
            partial(server.protocolClass.connectionLost.called, timeout=timeout)
        )
        self.cleanups['listens'].append(
            partial(maybeDeferred, server.port.stopListening)
        )

    def makeTCPClient(self, protocol, port, factory=None, when='connectionMade'):
        protocolClass = hook(protocol, when, 'connectionLost')
        if factory is None:
            factory = ClientFactory()
        factory.protocol = protocolClass
        connection = reactor.connectTCP('localhost', port.getHost().port, factory)
        client = TCPClient(
            protocolClass, connection, getattr(protocolClass, when).protocol()
        )
        self.cleanupTCPClient(client)
        return client

    def cleanupTCPClient(self, client, timeout=None):
        timeout = resolveTimeout(timeout)
        self.cleanups['connections'].extend((
            partial(maybeDeferred, client.connection.disconnect),
            partial(client.protocolClass.connectionLost.called, timeout=timeout),
        ))


