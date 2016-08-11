from errno import *

__author__ = 'admin'

from packet import *
import socket
import sys


class Connection:
    def __init__(self, reactor, sock=None, addr=None):
        self.reactor = reactor
        self.sock = sock
        self.address = addr
        self.packet = Packet()

    def listen(self, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setblocking(0)
        self.address = ('127.0.0.1', port)

        print >> sys.stderr, 'starting up on %s port %s' % self.address

        self.sock.bind(self.address)
        self.sock.listen(5)

    def connect(self, destination):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setblocking(0)
        self.address = destination

        print >> sys.stderr, 'connecting to %s port %s' % self.address

        err = self.sock.connect_ex(self.address)
        if err in (EINPROGRESS, EALREADY, EWOULDBLOCK):
            return
        if err not in (0, EISCONN):
            raise socket.error(err, errorcode[err])
        else:
            return

    def accept(self):
        try:
            sock, addr = self.sock.accept()
            sock.setblocking(0)
            return sock, addr
        except socket.error, why:
            if why.args[0] == EWOULDBLOCK:
                pass
            else:
                raise

    def write(self, data):
        try:
            result = self.sock.send(data)
            return result
        except socket.error, why:
            if why.args[0] == EWOULDBLOCK:
                return 0
            else:
                print 'write error: %d, %s' % (why.errno, why.strerror)
                self.handle_exception_event()
                return 0

    def read(self, buffer_size):
        try:
            data = self.sock.recv(buffer_size)
            size = len(data)
            if not data:
                self.handle_exception_event()
                return ''
            else:
                return data

        except socket.error, why:
            self.handle_exception_event()
            print 'receive error:%d, %s' % (why.errno, why.strerror)
            return ''

    def close(self):
        self.connected = False
        self.accepting = False
        try:
            self.sock.close()
        except socket.error, why:
            if why.args[0] not in (ENOTCONN, EBADF):
                raise

    def is_event_coming(self, selected_sock):
        if self.sock is selected_sock:
            return True
        else:
            return False

    def handle_read_event(self):
        pass

    def handle_write_event(self):
        pass

    def handle_exception_event(self):
        pass
