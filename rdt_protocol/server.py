from rdt2 import socket

CLIENT_ADDR = ('127.0.0.1', 5556)
server = socket()

server.bind(('127.0.0.1', 5555))

while True:
    data = server.recv(CLIENT_ADDR)
    print('======',data,'=========')
    if not data:
        break
    server.send(data, CLIENT_ADDR)
