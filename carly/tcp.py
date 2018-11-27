from attr import make_class
from twisted.internet.defer import (
    inlineCallbacks, gatherResults, returnValue
)
from twisted.internet.protocol import Factory, ClientFactory

from .hook import hook

TCPClient = make_class('TCPClient', ['protocolClass', 'connection',
                                     'clientProtocol', 'serverProtocol'])

class TCPServer(object):

    def __init__(self, protocolClass, port):
        self.protocolClass = protocolClass
        self.port = port
        host = self.port.getHost()
        self.targetHost = host.host
        self.targetPort = host.port


def makeTCPServer(context, protocol, factory=None, interface='127.0.0.1',
                  installProtocol=True):

    from twisted.internet import reactor

    hook(protocol, 'connectionMade')
    if factory is None:
        factory = Factory()
    if installProtocol:
        factory.protocol = protocol
    port = reactor.listenTCP(0, factory, interface=interface)
    server = TCPServer(protocol, port)
    hook(server.protocolClass, 'connectionLost', once=True)
    context.cleanupServers(server.port)
    return server


def disconnect(client):
    client.connection.disconnect()


@inlineCallbacks
def makeTCPClient(context, protocol, server, factory=None,
                  when='connectionMade', close=disconnect):

    from twisted.internet import reactor

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
    hook(client.protocolClass, 'connectionLost', once=True)
    context.cleanupClient(client, close)
    returnValue(client)
