from twisted.internet.protocol import Factory
from twisted.internet.task import LoopingCall
from twisted.protocols.basic import LineReceiver


class Chat(LineReceiver):

    delimiter = b'\n'

    def __init__(self, users):
        self.users = users
        self.name = None
        self.state = "GETNAME"

    def connectionMade(self):
        self.sendLine("What's your name?")

    def connectionLost(self, reason):
        if self.name in self.users:
            del self.users[self.name]

    def lineReceived(self, line):
        if self.state == "GETNAME":
            self.handle_GETNAME(line)
        else:
            self.handle_CHAT(line)

    def handle_GETNAME(self, name):
        if name in self.users:
            self.sendLine("Name taken, please choose another.")
            return
        self.sendLine("Welcome, %s!" % (name,))
        self.name = name
        self.users[name] = self
        self.state = "CHAT"

    def handle_CHAT(self, message):
        message = "<%s> %s" % (self.name, message)
        for name, protocol in self.users.iteritems():
            if protocol != self:
                protocol.sendLine(message)


class ChatFactory(Factory):

    loop = None

    def __init__(self):
        self.users = {} # maps user names to Chat instances
        self.count = 0

    def buildProtocol(self, addr):
        return Chat(self.users)

    def tick(self):
        for protocol in self.users.values():
            protocol.sendLine('<tick> '+str(self.count))
        self.count += 1

    def start(self, tickInterval=1) :
        self.loop = LoopingCall(self.tick)
        self.loop.start(tickInterval)

    def stop(self):
        if self.loop.running:
            self.loop.stop()
