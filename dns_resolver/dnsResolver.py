from socket import *
import dns.resolver
import dns.message
import time
from parse_header import DNSHeader
serverPort = 12000
# https://en.wikipedia.org/wiki/List_of_DNS_record_types
TYPE = {
    b"\x00\x01": "A",
    b"\x00\x1c": "AAAA",
    b"\x00\x05": "CNAME",
    b"\x00\x0c": "PTR",
    b"\x00\x10": "TXT",
    b"\x00\x0f": "MX",
    b"\x00\x06": "SOA"
}

class DNS_Resolver:
    def get_query_content(self, data):
        querys = []
        dns_header = DNSHeader()
        dns_header.parse_header(data)
        # get the number of question
        q_count = dns_header.__dict__.get('QDCount')
        # query part starts at 12th byte
        pointer = 12
        for i in range(q_count):
            query = {
                'name':[],
                'qtype':''
            }
            # get the length of next part of name
            length = data[pointer]
            # iterate until get the full name part
            while(length!=0):
                start = pointer+1
                end = pointer + length + 1
                query['name'].append(data[start:end])
                pointer += length+1
                length = data[pointer]
            # get the query type
            query['qtype'] = data[pointer+1:pointer+3]
            # get the query class
            query['qclass'] = data[pointer+3:pointer+5]
            pointer += 5
            querys.append(query)
        return querys
    
    def get_domain_name(self, name_slice):
        # transfer byte format to str format
        name = ''
        count = 0
        for slice in name_slice:
            name += slice.decode()
            count += 1
            if count != len(name_slice):
                name += '.'
        return name 

if __name__ == '__main__':
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    serverSocket.bind(('', serverPort))
    # maintain a cache
    cache = {}
    print("The server is ready to receive")
    while True:
        data, clientAddress = serverSocket.recvfrom(2048)
        dns_resolver = DNS_Resolver()
        querys = dns_resolver.get_query_content(data)
        header = DNSHeader()
        header.parse_header(data)
        # get the query id, name, type
        ID = header.ID
        name = dns_resolver.get_domain_name(querys[0].get('name'))
        qtype = TYPE.get(querys[0].get('qtype'))
        # flag indicated whether the cached item is expired
        flag = 0
        if cache.get((name, qtype)) is not None:
            cur_time = time.time()
            pre_time = cache.get((name, qtype))[1]
            # calculate total cached time of one item
            elapse = cur_time - pre_time
            # get the reponse content from cache
            response = cache.get((name, qtype))[0]
            response_message = dns.message.from_wire(response)
           
            for answer in response_message.answer:
                if elapse > answer.ttl:
                    flag = 1
                    break
            # if one of the rdata is expired, do the query again
            if flag == 1:
                serverSocket.sendto(data, ('ns2.sustc.edu.cn', 53))
                response, dns_address = serverSocket.recvfrom(2048) 
                response_message = dns.message.from_wire(response)
                cache[(name, qtype)] = (response, time.time())
            else:
                print("cache hit")
                response_arr = bytearray(response)
                # modify the response id
                response_arr[0] = data[0]
                response_arr[1] = data[1]
                response = bytes(response_arr)
        else:
            # send the query to upstream dns server
            serverSocket.sendto(data, ('ns2.sustc.edu.cn', 53))
            response, dns_address = serverSocket.recvfrom(2048) 
            response_message = dns.message.from_wire(response)
            # push the rdata to cache, and record the current time
            cache[(name, qtype)] = (response, time.time())
        serverSocket.sendto(response, clientAddress)   
    

