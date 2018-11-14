from rdt2 import socket
SERVER_ADDR = ('127.0.0.1', 5555)
client = socket()

client.bind(('127.0.0.1', 5556))
str = ''
for i in range(0, 5):
    str += 'computer network is so interesting'
data = str.encode()
client.send(data,SERVER_ADDR)
data = client.recv(SERVER_ADDR)
print(data)