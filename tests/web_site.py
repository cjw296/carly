from time import sleep

from autobahn.twisted import WebSocketServerProtocol, WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource
from twisted.internet.defer import inlineCallbacks
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.web.resource import EncodingResourceWrapper
from twisted.web.server import Site, GzipEncoderFactory
from twisted.web.static import File


class ServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        self.factory.state.clients.add(self)

    def blockingSendMessage(self):
        # simulate blocking work such as a SQLAlchemy query:
        sleep(self.factory.state.respondDuration)
        self.sendMessage(self.factory.state.ack, isBinary=False)

    @inlineCallbacks
    def onMessage(self, payload, isBinary):
        if isBinary:
            self.sendClose(4000, u'No binary please')
        else:
            yield deferToThread(self.blockingSendMessage)


class WebSocketState(object):

    count = 0

    def __init__(self, ack, sendDuration=0.01, respondDuration=0.01):
        self.ack = ack
        self.sendDuration = sendDuration
        self.respondDuration = respondDuration
        self.clients = set()
        self.factory = WebSocketServerFactory()
        self.factory.protocol = ServerProtocol
        self.factory.state = self
        LoopingCall(self.ping).start(2, now=False)

    def blockingSendMessage(self):
        # simulate blocking work such as a SQLAlchemy query:
        sleep(self.sendDuration)
        self.count += 1
        for client in self.clients:
            client.sendMessage('ping '+str(self.count))

    def ping(self):
        deferToThread(self.blockingSendMessage)


def buildSite(ack, staticPath):
    state = WebSocketState(ack)
    websocket = WebSocketResource(state.factory)
    static = EncodingResourceWrapper(File(staticPath), [GzipEncoderFactory()])
    static.putChild('spam', websocket)
    return Site(static)
