import socket
import struct
import sys
import uuid
import datetime
import json
import requests

def getCoord():
    send_url = 'http://api.ipstack.com/check?access_key=40132d177eb8526286574cccdd93d96c'
    r = requests.get(send_url)
    j = json.loads(r.text)
    lat = j['latitude']
    lon = j['longitude']
    # print(j)

    return lat, lon

message = {}

lat, lon = getCoord()
message['coord'] = {'lat': lat, 'lon': lon}
message['dist_threshold'] = input("dist_threshold: ")
message['hop'] = int(input("hop: "))

message['message'] = input("message: ")

lifetime = int(input("lifetime in seconds: "))
message['expired_at'] = datetime.datetime.now() + datetime.timedelta(0, lifetime)

message['uuid'] = uuid.uuid1()

myname = socket.getfqdn(socket.gethostname())
print(myname)
myaddr = socket.gethostbyname(myname)
print(myaddr)
message['src_address'] = myaddr

multicast_group = ('224.3.29.71', 10000)

# Create the datagram socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set a timeout so the socket does not block indefinitely when trying
# to receive data.
sock.settimeout(0.2)

# Set the time-to-live for messages to 1 so they do not go past the
# local network segment.
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:
    # Send data to the multicast group
    print('sending message...')
    message = json.dumps(message, default=str)
    sent = sock.sendto(message.encode('UTF-8'), multicast_group)

    # Look for responses from all recipients
    while True:
        print('waiting to receive')
        try:
            data, server = sock.recvfrom(16)
        except socket.timeout:
            print('timed out, no more responses')
            break
        else:
            print('received "%s" from %s' % (data, server))

finally:
    print('closing socket')
    sock.close()