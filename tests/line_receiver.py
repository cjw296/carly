from twisted.internet.protocol import Protocol
from twisted.protocols.basic import LineReceiver


class EchoServer(Protocol):

    def dataReceived(self, data):
        """
        As soon as any data is received, write it back.
        """
        self.transport.write(data)


class EchoClient(LineReceiver):

    end = b"Bye-bye!"

    def connectionMade(self):
        self.sendLine(b"Hello, world!")
        self.sendLine(b"What a fine day it is.")
        self.sendLine(self.end)

    def lineReceived(self, line):
        print("receive:", line)
        if line == self.end:
            self.transport.loseConnection()
