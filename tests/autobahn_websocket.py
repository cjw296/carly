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
        print("WebSocket connection open.")

        while True:
            print("Sending Messages")
            self.sendMessage(u"Hello, world!".encode('utf8'))
            self.sendMessage(b"\x00\x01\x03\x04", isBinary=True)
            yield sleep(1)

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            print("Text message received: {0}".format(payload.decode('utf8')))
