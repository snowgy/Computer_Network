def make_pkt(seq_num, data, checksum):
    '''
        make the packet to be send (contains three part)
    '''
    seq_bytes = seq_num.to_bytes(4, byteorder = 'little', signed = True)
    check_sum_bytes = checksum.to_bytes(2, byteorder = 'little', signed = True)
    return seq_bytes + data + check_sum_bytes

def unpack(packet):
    '''
        unpack packet to get sequence number and payload
    '''
    seq_num = int.from_bytes(packet[0:4], byteorder = 'little', signed = True)
    data = packet[4:-2]
    checksum = int.from_bytes(packet[-2:], byteorder = 'little', signed = True)
    return seq_num, data, checksum

def make_empty_pkt():
    return b''


