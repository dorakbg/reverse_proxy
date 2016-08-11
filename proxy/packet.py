import struct

PACKET_HEADER_LENGTH = 15


class Packet:
    commands = {
        'unknown': 0,
        'open': 1,
        'opened': 2,
        'close': 3,
        'closed': 4,
        'data': 5
    }

    def __init__(self):
        global PACKET_HEADER_LENGTH
        self.buf = None
        self.next_seq = 0
        self.queue = []
        self.out_seq = 0
        self.hdr_len = PACKET_HEADER_LENGTH

    def pack(self, id, type, payload):
        print "send packet <%s, %d, %d>" % (type, id, len(payload))
        hdr = struct.pack('!QLHB', self.out_seq, id, len(payload), self.commands[type])
        self.out_seq += 1
        return hdr + payload

    def unpack(self, data):
        command = None
        if self.buf == None:
            self.buf = data
        else:
            self.buf += data

        in_len = len(self.buf)

        if in_len < self.hdr_len:
            print 'received partial packet with size: %d ' % in_len
            return None

        seq, id, payload_size, type = struct.unpack('!QLHB', self.buf[:self.hdr_len])
        packet_size = payload_size + self.hdr_len

        if packet_size > in_len:
            return None

        payload = self.buf[self.hdr_len:packet_size]

        if in_len > packet_size:
            self.buf = self.buf[packet_size:-1]
        else:
            self.buf = None

        if type > len(self.commands):
            command = 'unknown'
        else:
            for (c, t) in self.commands.items():
                if t == type:
                    command = c
                    break

        packet = (seq, command, id, payload)
        return packet

    def output(self, packet):
        out_queue = []
        num = len(self.queue)

        seq = packet[0]

        if seq == self.next_seq:
            self.next_seq = seq + 1
            out_queue.append(packet)

            if num == 0:
                return out_queue
            else:
                for i in range(num, -1, -1):
                    if self.queue[i][0] == self.next_seq:
                        self.next_seq += 1
                        out_queue.append(packet)
                        self.queue.remove(i)
                return out_queue

        if num == 0:
            self.queue.insert(0, packet)
        else:
            for i in range(num, -1, -1):
                if self.queue[i][0] > seq:
                    self.queue.insert(i + 1, packet)

        return None
