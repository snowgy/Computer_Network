import asyncio
import os
from parse_header import HTTPHeader
from mime_type import types
from urllib.parse import unquote

async def dispatch(reader, writer):
    header = HTTPHeader()
    query = {}
    text = None
    File = None
    flag = 0
    file_not_found = 0
    count = 0
    last_dir = './'
    while True:
        data = await reader.readline()
        message = data.decode()
        if data == b'\r\n':
            break
        if count == 0:
            header.parse_header(message)
            path = header.get('path')
            method = header.get('method')
        else:
            k, v = message.split(': ')
            v = v.replace("\r\n","")
            query[k] = v
        count = count + 1
    print(query)
    if method != 'GET' and method != 'HEAD':
        flag = 1
       
    if header.get('path') is not None:
        path = './' + header.get('path')
    else:
        path = './/'
    path = path[:-1]
    path = unquote(path)
    if not os.path.isfile(path):
        if os.path.isdir(path):
            text = html_render(path)
        else:
            file_not_found = 1
           
    else:
        File = open(path,"rb+")
    if 'Cookie' in query:
        cookie = query['Cookie']
        print(cookie)
        last_dir = cookie.split('last_dir=')[1]
    print(last_dir)
    if path == './':
        print("redirect")
        if(last_dir != './' and last_dir != '..'):
            res = last_dir.split('./')[1]
            print(last_dir)
            writer.writelines([
                b'HTTP/1.0 302 Found\r\n',
                b'Location: '+b'http://127.0.0.1:8080'+res.encode()+b'/'+b'\r\n',
                b'Connection: close\r\n',
                b'\r\n',
            ])

    if flag == 1:
        writer.writelines([
                b'HTTP/1.0 405 Method Not Allowed\r\n',
                b'Content-Type:text/html; charset=utf-8\r\n',
                b'Connection: close\r\n',
                b'\r\n',
                b'<html><body>HTTP/1.0 405 Method Not Allowed<body></html>\r\n',
                b'\r\n'
            ])
    else:
        if text is not None:
            writer.writelines([
                b'HTTP/1.0 200 OK\r\n',
                b'Content-Type:text/html; charset=utf-8\r\n',
                b'Connection: close\r\n',
                b'Set-Cookie: last_dir='+path.encode()+b';path=/;'+b'\r\n',
                b'\r\n',
                text.encode()+b'\r\n',
                b'\r\n'
            ])
        else:
            last_dir = os.path.pardir
            if file_not_found:
                writer.writelines([
                    b'HTTP/1.0 404 Not Found\r\n',
                    b'Content-Type:text/html; charset=utf-8\r\n',
                    b'Connection: close\r\n',
                    b'Set-Cookie: last_dir='+last_dir.encode()+b';path=/;'+b'\r\n',
                    b'\r\n',
                    b'<html><body>HTTP/1.0 404 Not Found<body></html>\r\n',
                    b'\r\n'  
                ])
            else:
                content = File.read()
                length = str(os.path.getsize(path))
                tmp = path.split('.')
                suffix = tmp[-1]
                mime_type = types.get(suffix)
                if mime_type is None:
                    mime_type = 'application/octet-stream'
                if 'Range' in query:
                    range_str = query['Range'].split('=')[1]
                    print(range_str)
                    s, e = range_str.split('-')
                    s = int(s)
                    if e is not '':
                        e = int(e)
                    else:
                        e = int(length)-1
                    content_length = e-s+1
                    File.seek(s,0)
                    if e is not '':
                        p_content = File.read(e-s+1)
                    else:
                        p_content = File.read()
                    writer.writelines([
                        b'HTTP/1.0 206 Partial Content\r\n',
                        b'Content-Type: '+mime_type.encode()+b'; charset=utf-8\r\n',
                        b'Content-Length: '+str(content_length).encode()+b'\r\n',
                        b'Content-Range: bytes '+ str(s).encode()+b'-'+str(e).encode()+ b'/'+length.encode()+b'\r\n',
                        b'Connection: keep-alive\r\n',
                        b'Set-Cookie: last_dir='+last_dir.encode()+b';path=/;'+b'\r\n',
                        b'\r\n',
                        p_content
                    ])
                else:
                    writer.writelines([
                        b'HTTP/1.0 200 OK\r\n',
                        b'Content-Type: '+mime_type.encode()+b'; charset=utf-8\r\n',
                        b'Content-Length: '+length.encode()+b'\r\n',
                        b'Connection: close\r\n',
                        b'Set-Cookie: last_dir='+last_dir.encode()+b'path=/;'+b'\r\n',
                        b'\r\n',
                        content
                    ])
    writer.close()
    if File:
        File.close()

def html_render(path):
    dirs = os.listdir(path)
    text = "<html><head><title>Index of"+path+"</title></head>"+\
           "<body bgcolor=\"white\">"+\
           "<h1>Index of"+path+"</h1><hr><pre>"
    for directory in dirs:
        text += "<a href=\""+directory+"/\">"+directory+"/</a><br>"
    text += "</pre><hr></body></html>"
    return text

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, '127.0.0.1', 8080, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
