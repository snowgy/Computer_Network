from udp import UDPsocket
from packet import *
from timer import Timer
import random
import time
import _thread
import threading
import signal

BUFFER_SIZE = 100
PACKET_SIZE = 20
TIMEOUT_INTERVAL = 2
SLEEP_INTERVAL = 1
WINDOW_SIZE = 4
data_buffer = b''

#base = 0
send_timer = Timer(TIMEOUT_INTERVAL)
address = ('127.0.0.1', 5555)

class socket(UDPsocket):
    #send_finish = 0
    base = 0
    pkt_num = 0
    def send(self, data, ADDR):
        address = ADDR
        print('send to ',address)
        packets = []
        seq_num = 0
        #data = data.encode(encoding='utf-8')
        #self.pkt_num = int(len(data)/PACKET_SIZE)+ 1
        self.set_pkt_num(int(len(data)/PACKET_SIZE)+ 1)
        '''
            slice the data into packets and put them into the buffer
        '''
        for i in range(0, self.pkt_num):
            data_slice = data[i*PACKET_SIZE : (i+1)*PACKET_SIZE]
            seq_bytes = seq_num.to_bytes(4, byteorder = 'little', signed = True)
            check_sum = socket._get_checksum(self, seq_bytes + data_slice)
            packets.append(make_pkt(seq_num, data_slice, check_sum))
            seq_num += 1
        next_seq = 0
        print(self.pkt_num)
        # start sender receive thread
        #_thread.start_new_thread(socket._sender_recv, (self,))
        #t.start()
        while(self.base < self.pkt_num):
            #print(base)
            #lock.acquire()
            #print(next_seq)
            # send all pkts in the window
            while next_seq < self.base + WINDOW_SIZE and next_seq < self.pkt_num:
                print('sending pkt ', next_seq)
                UDPsocket.send(UDPsocket,packets[next_seq],address)
                # if next sequence number is equal to base, start timer
                next_seq += 1
            if not send_timer.running():
                print('start timer')
                send_timer.start()
            # wait for ack or timeout. we now release the lock and _sender_recv thread can do modification
            while send_timer.running() and not send_timer.timeout():
                #lock.release()
                print("Waiting...")
                socket._sender_recv(self)
                #time.sleep(SLEEP_INTERVAL)
                #lock.acquire()
            # handle timeout
            if send_timer.timeout():
                print("Time out")
                send_timer.stop()
                # resend every packet from base
                next_seq = self.base
            #lock.release()
        print('======finish send========')
    
        for i in range(0, 5):
            time.sleep(SLEEP_INTERVAL)
            UDPsocket.send(UDPsocket, make_pkt(0, b'', 0), address)
            print('=======sender send empty packet==========')
        
        #socket.set_flag()
        self.base = 0

    def recv(self, ADDR):
        expected_num = 0
        address = ADDR
        global data_buffer
        while True:
            # get the next packet from sender
            '''
            print(socket.send_finish)
            if socket.send_finish == 1:
                socket.clear_flag()
                break
            '''
            #time.sleep(1)
            pkt = UDPsocket.recv(self, BUFFER_SIZE)
            if pkt is None:
                continue
            #print('recv ', len(pkt))
            seq_num, data, checksum = unpack(pkt)
            
            if checksum == 0 and seq_num ==0:
                print('recv empty packet finish recv')
                break
            
            print("recv packet ", seq_num)
            #print('original checksum ', checksum)
            pkt_checksum = socket._get_checksum(self, pkt[0: -2])
            #print('recv checksum ', pkt_checksum)
           
            is_corrupt = not (checksum == pkt_checksum)
            print('is corrupt ', is_corrupt)
            # send an ack
            if seq_num == expected_num and not is_corrupt:
                print("Got expected pkt ",seq_num)
                print('Sending ACK', expected_num,'TO',address)
                data_buffer += pkt[4:-2]
                _data = expected_num.to_bytes(4, byteorder = 'little', signed = True)
                UDPsocket.send(UDPsocket, make_pkt(expected_num, b'', socket._get_checksum(self, _data)), address)
                expected_num += 1
            elif seq_num > 0:
                # send ack on previous acked packet
                pre_expected_num = expected_num - 1
                _data = pre_expected_num.to_bytes(4, byteorder = 'little', signed = True)
                print('Sending dup ACK', expected_num-1)
                UDPsocket.send(UDPsocket, make_pkt(pre_expected_num, b'', socket._get_checksum(self, _data)), address)
        print('==========recv finished===========')
        return data_buffer

    def _get_checksum(self, data):
        '''
        calculate checksum
        '''
        check_sum = 0
        data_length = len(data)
        for i in range(0, data_length):
            tmp = int.from_bytes(data[i:i+1], byteorder='big')
            check_sum += tmp
        check_sum = -(check_sum % 256)
        return (check_sum & 0xFF)

    def _sender_recv(self):
        print('start recv')
        #global base
        global send_timer
        pkt = None
        #global lock
        sleep_time = random.random()
        time.sleep(sleep_time)
        signal.signal(signal.SIGALRM, recv_timeout_handler)
        try:
            signal.alarm(2)
            pkt = UDPsocket.recv(self, BUFFER_SIZE)
            if pkt:
                signal.alarm(0)
        except RuntimeError as e:
            print("recv time out")
            signal.alarm(0)
            
        if pkt is None:
            return
        ack, _data, checksum = unpack(pkt)
        print('recv ack ', ack)
        pkt_checksum = socket._get_checksum(self, pkt[0: -2])
        is_corrupt = not (checksum == pkt_checksum)
        print('is_corrupt ', is_corrupt )
        #print('base', self.base)
        if not is_corrupt and ack >= self.base and checksum!=0:
            #lock.acquire()
            self.base = ack + 1        
            print('base update ', self.base)
            #print('pkt num ', self.pkt_num)
            if self.base == self.pkt_num:
                return
            send_timer.stop()
            #lock.release()

    @classmethod
    def set_flag(self):
        self.send_finish = 1
        return self.send_finish
    @classmethod
    def clear_flag(self):
        self.send_finish = 0
        return self.send_finish
    @classmethod
    def set_pkt_num(self, pkt_num):
        self.pkt_num = pkt_num

def recv_timeout_handler(signum, frame):
        print('time out')
        raise RuntimeError

