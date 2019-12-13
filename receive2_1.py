import socket
import struct
import sys
import json
import datetime
import requests
import math
    
def getCoord():
    send_url = 'http://api.ipstack.com/check?access_key=40132d177eb8526286574cccdd93d96c'
    r = requests.get(send_url)
    j = json.loads(r.text)
    lat = j['latitude']
    lon = j['longitude']

    return lat, lon


def caldist(destlatitude, destlongitude):
    #calculating the geographical distance using the latiude and longitude of both my computer and destination
    #the earth is abstracted in to a sphere
    distance = 0
    earthR = 6371.0 #the radius of earth is abstracted t o 6371 kilometers in this program
    myla, mylo = getCoord()
    myla = math.radians(myla)
    mylo = math.radians(mylo)
    destla = math.radians(destlatitude)
    destlo = math.radians(destlongitude)
    deltaphi = myla - destla
    deltalambda = mylo - destlo
    phim = (myla + destla)/2
    distance = earthR*math.sqrt(math.pow(deltaphi,2) + (math.cos(phim)*math.pow(deltalambda,2)))
    return distance

multicast_group = '224.3.29.72'
server_address = ('', 9999)

# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind to the server address
sock.bind(server_address)

# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

uuids = []
messages = []

print('sending acknowledgement to', ('224.3.29.72', 10000))
message = 'ack'
sock.sendto(message.encode('UTF-8'), ('224.3.29.72', 10000))

lat_from = -7.37929
lon_from = 112.7040363

next_group_addr = ('224.3.29.73', 9998)

# Receive/respond loop
while True:
    print('waiting to receive message')
    data, address = sock.recvfrom(1024)

    try:
        data = json.loads(data)
    except:
        data = data.decode()
        
    # if (address != socket.gethostbyname(socket.gethostname())):
    if(data == 'ack'):
        print('received %s bytes from %s' % (data, address))
        for message in messages:
            distance = caldist(lat_from, lon_from)

            if(distance <= float(message['dist_threshold'])):
                if(datetime.datetime.strptime(message['expired_at'], '%Y-%m-%d %H:%M:%S.%f') > datetime.datetime.now()):
                    print('sending message to', address)
                    sock.sendto(json.dumps(message).encode('UTF-8'), address)
                else:
                    messages.remove(message)
                    uuids.remove(message['uuid'])
    else:
        # lat_from = data['coord']['lat']
        # lon_from = data['coord']['lon']
        
        distance = caldist(lat_from, lon_from)
        print(distance)

        if(distance <= float(data['dist_threshold'])):
            if(datetime.datetime.strptime(data['expired_at'], '%Y-%m-%d %H:%M:%S.%f') > datetime.datetime.now()):
                if(data['uuid'] not in uuids):
                    uuids.append(data['uuid'])
                    messages.append(data)

                    print('received %s bytes from %s with distance %s' % (data, address, distance))
                    print(". . .")

        if(int(data['hop']) - 1 > 0):
            data['hop']  = int(data['hop']) - 1
            sock.sendto(json.dumps(data).encode('UTF-8'), next_group_addr)
        else:
            print("batas hop, tidak meneruskan ke next address")