from functools import partial

from collections import namedtuple

from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, gatherResults, \
    maybeDeferred, returnValue
from twisted.internet.protocol import Factory, ClientFactory

from .hook import hook, hookMethod
from .timeout import resolveTimeout

TCPServer = namedtuple('TCPServer', ['protocolClass', 'port'])
TCPClient = namedtuple('TCPClient', ['protocolClass', 'connection',
                                     'clientProtocol', 'serverProtocol'])


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

    def makeTCPServer(self, protocol, factory=None, interface='127.0.0.1'):
        protocolClass = hook(protocol, 'connectionMade')
        if factory is None:
            factory = Factory()
        factory.protocol = protocolClass
        port = reactor.listenTCP(0, factory, interface=interface)
        server = TCPServer(protocolClass, port)
        self.cleanupTCPServer(server)
        return server

    def cleanupTCPServer(self, server):
        hookMethod(server.protocolClass, 'connectionLost', once=True)
        self.cleanups['listens'].append(
            partial(maybeDeferred, server.port.stopListening)
        )

    @inlineCallbacks
    def makeTCPClient(self, protocol, server, factory=None, when='connectionMade'):
        protocolClass = hook(protocol, when)
        if factory is None:
            factory = ClientFactory()
        factory.protocol = protocolClass
        connection = reactor.connectTCP('localhost', server.port.getHost().port, factory)
        clientProtocol, serverProtocol = yield gatherResults([
            getattr(protocolClass, when).protocol(),
            server.protocolClass.connectionMade.protocol(),
        ])
        client = TCPClient(protocolClass, connection, clientProtocol, serverProtocol)
        self.cleanupTCPClient(client)
        returnValue(client)

    def cleanupTCPClient(self, client, timeout=None, when='connectionLost'):
        hookMethod(client.protocolClass, when, once=True)
        timeout = resolveTimeout(timeout)
        self.cleanups['connections'].extend((
            partial(maybeDeferred, client.connection.disconnect),
            partial(client.clientProtocol.connectionLost.called, timeout=timeout),
            partial(client.serverProtocol.connectionLost.called, timeout=timeout),
        ))


