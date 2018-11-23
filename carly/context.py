from attr import make_class
from functools import partial
from twisted.internet import reactor
from twisted.internet.defer import (
    inlineCallbacks, gatherResults, maybeDeferred, returnValue
)
from twisted.internet.protocol import Factory, ClientFactory, DatagramProtocol

from .clock import withTimeout, cancelDelayedCalls
from .hook import hook, cleanup

TCPClient = make_class('TCPClient', ['protocolClass', 'connection',
                                     'clientProtocol', 'serverProtocol'])

class TCPServer(object):

    def __init__(self, protocolClass, port):
        self.protocolClass = protocolClass
        self.port = port
        host = self.port.getHost()
        self.targetHost = host.host
        self.targetPort = host.port


class UDP(DatagramProtocol):

    def __init__(self, port, protocol):
        self.port = port
        self.protocol = protocol
        host = self.port.getHost()
        self.targetHost = host.host
        self.targetPort = host.port

    def startProtocol(self):
        self.transport.connect(self.targetHost, self.targetPort)

    def send(self, datagram):
        self.transport.write(datagram)


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
            withTimeout(d, timeout)
        return gatherResults(deferreds)

    @inlineCallbacks
    def cleanup(self, timeout=None, delayedCalls=None):
        yield self._cleanup(self.cleanups['connections'], timeout)
        yield self._cleanup(self.cleanups['listens'], timeout)
        cleanup()
        if delayedCalls:
            cancelDelayedCalls(delayedCalls)

    def cleanupServers(self, *ports):
        self.cleanups['listens'].extend(
            partial(maybeDeferred, port.stopListening) for port in ports
        )

    def makeTCPServer(self, protocol, factory=None, interface='127.0.0.1',
                      installProtocol=True):
        hook(protocol, 'connectionMade')
        if factory is None:
            factory = Factory()
        if installProtocol:
            factory.protocol = protocol
        port = reactor.listenTCP(0, factory, interface=interface)
        server = TCPServer(protocol, port)
        self.cleanupTCPServer(server)
        return server

    def cleanupTCPServer(self, server):
        hook(server.protocolClass, 'connectionLost', once=True)
        self.cleanupServers(server.port)

    @inlineCallbacks
    def makeTCPClient(self, protocol, server, factory=None, when='connectionMade'):
        hook(protocol, when)
        if factory is None:
            factory = ClientFactory()
        factory.protocol = protocol
        host = server.port.getHost()
        connection = reactor.connectTCP(host.host, host.port, factory)
        clientProtocol, serverProtocol = yield gatherResults([
            getattr(protocol, when).protocol(),
            server.protocolClass.connectionMade.protocol(),
        ])
        client = TCPClient(protocol, connection, clientProtocol, serverProtocol)
        self.cleanupTCPClient(client)
        returnValue(client)

    def cleanupTCPClient(self, client, timeout=None, when='connectionLost'):
        hook(client.protocolClass, when, once=True)
        self.cleanups['connections'].extend((
            partial(maybeDeferred, client.connection.disconnect),
            partial(client.clientProtocol.connectionLost.called, timeout=timeout),
            partial(client.serverProtocol.connectionLost.called, timeout=timeout),
        ))

    def makeUDP(self, protocol, interface='127.0.0.1'):
        hook(protocol.__class__, 'datagramReceived')
        port = reactor.listenUDP(0, protocol, interface)
        udp = UDP(port, protocol)
        sendPort = reactor.listenUDP(0, udp, interface)
        self.cleanupServers(port, sendPort)
        return udp

