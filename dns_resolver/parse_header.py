import struct
class DNSHeader:
    Struct = struct.Struct('!6H')
    def __init__(self):
        self.__dict__ = {
            field: None
            for field in ('ID', 'QR', 'OpCode', 'AA', 'TC', 'RD', 'RA', 'Z', 'RCode', 'QDCount', 'ANCount', 'NSCount', 'ARCount')}
    def parse_header(self, data):
        self.ID, misc, self.QDCount, self.ANcount, \
        self.NScount, self.NScount = DNSHeader.Struct.unpack_from(data) 
        self.QR = (misc & 0x8000) != 0
        self.OpCode = (misc & 0x7800) >> 11
        self.AA = (misc & 0x0400) != 0
        self.TC = (misc & 0x200) != 0
        self.RD = (misc & 0x100) != 0
        self.RA = (misc & 0x80) != 0
        self.Z = (misc & 0x70) >> 4 # Never used
        self.RCode = misc & 0xF
    def __str__(self):
        return '<DNSHeader {}>'.format(str(self.__dict__))
