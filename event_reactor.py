import select
import threading
from connection import *


class EventReactor(threading.Thread):
    index = 0

    @staticmethod
    def gen_id():
        EventReactor.index += 1
        return EventReactor.index

    def __init__(self):
        self.read_queue = []
        self.write_queue = []
        super(EventReactor, self).__init__(name='event_reactor')
        self.lock = threading.Lock()

    def add(self, queue_type, connection):
        self.lock.acquire()

        if queue_type == 'read' and connection not in self.read_queue:
            self.read_queue.append(connection)
        elif queue_type == 'write' and connection not in self.write_queue:
            self.write_queue.append(connection)

        self.lock.release()

    def remove(self, connection):
        self.lock.acquire()

        if connection in self.read_queue:
            self.read_queue.remove(connection)
        elif connection in self.write_queue:
            self.write_queue.remove(connection)

        self.lock.release()

    def run(self):

        while True:

            self.lock.acquire()
            read_sock_queue = [item.sock for item in self.read_queue]
            write_sock_queue = [item.sock for item in self.write_queue]
            self.lock.release()

            readable, writable, exceptional \
                = select.select(read_sock_queue, write_sock_queue, read_sock_queue, 1)

            for s in readable:
                for connection in self.read_queue:
                    if connection.is_event_coming(s):
                        connection.handle_read_event()
                        break

            for s in writable:
                for connection in self.write_queue:
                    if connection.is_event_coming(s):
                        connection.handle_write_event()
                        break

            for s in exceptional:
                print >> sys.stderr, 'handling exceptional condition for', s.getpeername()
                for connection in self.read_queue:
                    if connection.is_event_coming(s):
                        connection.handle_exception_event()
                        break
