import json
from collections import Counter

from twisted.internet.protocol import DatagramProtocol
from twisted.internet.task import LoopingCall


class CollectorProtocol(DatagramProtocol):

    def __init__(self):
        self.counts = Counter()

    def datagramReceived(self, data, addr):
        payload = json.loads(data)
        self.counts[payload['id']] += 1


class SenderProtocol(DatagramProtocol):

    def __init__(self, targetIp, targetPort):
        self.counts = {}
        self.targetIp = targetIp
        self.targetPort = targetPort
        self.loop = LoopingCall(self.ping)

    def startProtocol(self):
        self.transport.connect(self.targetIp, self.targetPort)
        self.loop.start(1)
        self.sendDatagram()

    def ping(self):
        self.transport.write(json.dumps({'id': 'client'+str(id(self))}))
