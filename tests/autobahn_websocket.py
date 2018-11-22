from autobahn.twisted.util import sleep
from autobahn.twisted.websocket import WebSocketClientProtocol
from autobahn.twisted.websocket import WebSocketServerProtocol
from twisted.internet.defer import inlineCallbacks


class MyServerProtocol(WebSocketServerProtocol):

    def onMessage(self, payload, isBinary):
        if isBinary:
            self.sendClose(4000, u'No binary please')
        else:
            self.sendMessage(payload, isBinary=False)



class MyClientProtocol(WebSocketClientProtocol):

    @inlineCallbacks
    def onOpen(self):
        count = 0
        while True:
            count += 1
            self.sendMessage((u"tick "+str(count)).encode('utf8'))
            yield sleep(1)
