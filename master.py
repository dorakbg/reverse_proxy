__author__ = 'admin'

import random
import time

from config import *
from event_reactor import *


class Request(Connection):
    __queue = []

    @staticmethod
    def add(reactor, id, sock, source, destination):
        request = Request(reactor, id, sock, source, destination)
        Request.__queue.append(request)
        msg = request.packet.pack(request.id, 'open', request.destination)
        Tunnel.send_message(msg)

    @staticmethod
    def get(id):
        for req in Request.__queue:
            if req.id == id:
                return req

        print "unknown request id %d" % (id)
        return None


    def __init__(self, reactor, id, sock, source, destination):
        Connection.__init__(self, reactor, sock, source)
        self.destination = destination[0] + ':' + bytes(destination[1] + 1)
        self.id = id
        self.packet_queue =[]

    def process(self, packet):
        packets = self.packet.output(packet)
        if packets == None:
            return

        for (seq, cmd, id, payload) in packets:
            print 'receive new packet(%d, %s, %d, %d)' % (seq, cmd, id, len(payload))

            if cmd == 'unknown':
                self.handle_exception_event()

            elif cmd == 'opened':
                self.start()

            elif cmd == 'closed':
                print 'request session terminated'

            elif cmd == 'close':
                self.stop()

            elif cmd == 'data':
                self.write(payload)

    def delete(self):
        Request.__queue.remove(self)
        self.reactor.remove(self)
        self.close()
        print 'request <%s:%d> closed' % self.address

    def start(self):
        self.reactor.add('read', self)

    def stop(self):
        print 'terminate request <%s:%d>' % self.address
        msg = self.packet.pack(self.id, 'closed', '')
        Tunnel.send_message(msg)
        self.delete()

    def handle_read_event(self):
        data = self.read(2048)
        """
        if the data is null, exception occurred.
        """
        if len(data) == 0:
            return

        msg = self.packet.pack(self.id, 'data', data)
        Tunnel.send_message(msg)

    def handle_exception_event(self):
        msg = self.packet.pack(self.id, 'close', '')
        Tunnel.send_message(msg)
        self.delete()




class Tunnel(Connection):
    __queue = []

    def __init__(self, reactor, sock, source):
        Connection.__init__(self, reactor, sock, source)

    @staticmethod
    def add(reactor, sock, source):
        tunnel = Tunnel(reactor, sock, source)
        Tunnel.__queue.append(tunnel)
        reactor.add('read', tunnel)

    def handle_read_event(self):
        data = self.read(RECV_BUFF_SIZE)
        if len(data) == 0:
            return

        packet = self.packet.unpack(data)
        if packet == None:
            return

        id = packet[2]

        request = Request.get(id)
        if request == None:
            print 'unknown request %d recevies some data' % id
            return

        request.process(packet)

    def handle_exception_event(self):
        print "tunnel <%s:%d> is broken" % self.address
        Tunnel.__queue.remove(self)
        self.reactor.remove(self)
        self.close()

    @staticmethod
    def get():
        index_selected = random.randint(0, len(Tunnel.__queue) - 1)
        return Tunnel.__queue[index_selected]

    @staticmethod
    def send_message(msg):
        tunnel = Tunnel.get()
        tunnel.write(msg)


class TunnelMaster(Connection):
    def __init__(self, reactor, port):
        Connection.__init__(self, reactor)
        self.listen(port)
        reactor.add('read', self)

    def handle_read_event(self):
        sock, address = self.accept()
        Tunnel.add(self.reactor, sock, address)
        print "accept new tunnel %s:%d" % address

    def handle_exception_event(self):
        print 'TunnelMaster socket is broken!!!'
        self.reactor.remove(self)
        exit(-1)


class Proxyer(Connection):
    __queue = []

    def __init__(self, reactor, port):
        Connection.__init__(self, reactor)
        self.port = port
        self.listen(port)

    @staticmethod
    def add(reactor, port):
        proxy = Proxyer(reactor, port)
        Proxyer.__queue.append(proxy)
        reactor.add('read', proxy)

    def handle_read_event(self):
        sock, address = self.accept()
        destination = ('127.0.0.1', self.port)
        Request.add(self.reactor, EventReactor.gen_id(), sock, address, destination)

    def handle_exception_event(self):
        print 'Proxyer <:%d> is broken!!!' % self.port
        Proxyer.__queue.remove(self)
        self.reactor.remove(self)
        self.close()
        if len(Proxyer.__queue) == 0:
            print 'all proxy is broken, exit now!!!'
            exit(-1)


if __name__ == '__main__':

    reactor = EventReactor()
    reactor.setDaemon(True)
    reactor.start()

    time.sleep(1)

    tunnel_master = TunnelMaster(reactor, 5555)

    for port in [8079]:
        Proxyer.add(reactor, port)

    try:
        while (True):
            reactor.join(2)
            if not reactor.isAlive():
                break

    except KeyboardInterrupt:
        print('\nstopped by keyboard')
        exit(-1)
