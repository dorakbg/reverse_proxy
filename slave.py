__author__ = 'admin'

import random

from config import *
from event_reactor import *


class Request(Connection):
    __queue = []

    @staticmethod
    def add(reactor, id, destination):
        request = Request(reactor, id, destination)
        Request.__queue.append(request)
        reactor.add('write', request)

    @staticmethod
    def get(id):
        for req in Request.__queue:
            if req.id == id:
                return req

        print "unknown request id %d" % (id)
        return None

    def __init__(self, reactor, id, destination):
        Connection.__init__(self, reactor)
        self.id = id
        self.destination = destination
        self.connect(destination)

    def process(self, packet):
        packets = self.packet.output(packet)
        if packets == None:
            return

        for (seq, cmd, id, payload) in packets:

            print 'receive new packet(%d, %s, %d, %d)' % (seq, cmd, id, len(payload))

            if cmd == 'unknown':
                self.handle_exception_event()

            elif cmd == "data":
                self.write(payload)

            elif cmd == 'closed':
                self.delete()

            elif cmd == 'close':
                self.stop()

    def delete(self):
        Request.__queue.remove(self)
        self.reactor.remove(self)
        self.close()

    def stop(self):
        msg = self.packet.pack(self.id, 'closed', '')
        Tunnel.send_message(msg)
        self.delete()

    def handle_read_event(self):
        data = self.read(2048)
        if len(data) == 0:
            return

        msg = self.packet.pack(self.id, 'data', data)
        Tunnel.send_message(msg)

    def handle_write_event(self):
        self.reactor.remove(self)
        self.reactor.add('read', self)
        msg = self.packet.pack(self.id, 'opened', '')
        Tunnel.send_message(msg)

    def handle_exception_event(self):
        self.reactor.remove(self)
        msg = self.packet.pack(self.id, 'close', '')
        Tunnel.send_message(msg)
        print "request <%s:%d> is broken" % self.address


class Tunnel(Connection):
    __queue = []

    def __init__(self, reactor, destination):
        Connection.__init__(self, reactor)
        self.connect(destination)
        reactor.add('read', self)

    @staticmethod
    def add(reactor, destination):
        tunnel = Tunnel(reactor, destination)
        Tunnel.__queue.append(tunnel)

    def handle_read_event(self):
        data = self.read(RECV_BUFF_SIZE)
        if len(data) == 0:
            return

        packet = self.packet.unpack(data)
        if packet == None:
            return

        cmd = packet[1]
        id = packet[2]

        if cmd == 'open':
            payload = packet[3]
            address = payload.split(':')
            destination = (address[0], int(address[1]))
            Request.add(self.reactor, id, destination)

        request = Request.get(id)
        if request == None:
            print "unknown request id %d" % id
            return

        request.process(packet)

    def handle_exception_event(self):
        Tunnel.__queue.remove(self)
        self.reactor.remove(self)
        self.close()

        print "tunnel <%s:%d> is broken" % self.address

        if len(Tunnel.__queue) == 0:
            print "no tunnel exists, so exit.."
            exit(-1)

    @staticmethod
    def get():
        index_selected = random.randint(0, len(Tunnel.__queue) - 1)
        return Tunnel.__queue[index_selected]

    @staticmethod
    def send_message(msg):
        tunnel = Tunnel.get()
        tunnel.write(msg)


class Proxyer():
    def start(self, reactor, tunnel_num, port):
        destination = ('127.0.0.1', port)

        for i in range(0, tunnel_num):
            Tunnel.add(reactor, destination)


if __name__ == '__main__':

    reactor = EventReactor()
    reactor.setDaemon(True)
    reactor.start()

    proxyer = Proxyer()
    proxyer.start(reactor, 3, 5555)

    try:
        while (True):
            reactor.join(2)
            if not reactor.isAlive():
                break

    except KeyboardInterrupt:
        print('\nstopped by keyboard')
        exit(-1)
