import socket
import struct
import sys
import json
import datetime
import urllib.request
import math

def geoDistance(destaddress):
    #get the ip address of destination
    destaddr = destaddress
    #get the ip address of my computer
    myname = socket.getfqdn(socket.gethostname())
    myaddr = socket.gethostbyname(myname)
    #gather the latitude and longitude of hosts
    #we will use a default coordination
    (mylatitude, mylongitude) = getcoord(2, myaddr)
    mylatitude = float(mylatitude)
    mylongitude = float(mylongitude)
    #cannot get the geographical coordination of my computer using its current address, maybe because the computer is used within a NAT network.
    (destlatitude, destlongitude) = getcoord(1, destaddr)
    destlatitude = float(destlatitude)
    destlongitude = float(destlongitude)
    distance = caldist(mylatitude, mylongitude, destlatitude, destlongitude)
    return distance #distance in km
    


def getcoord(a, addr):
    #get the latitude and longitude of a given ip address
    host = 0
    if a == 1:
        host = "Destination host"
    if a == 2:
        host = "My computer"
    #send the http get request to http://freegeoip.net
    url = "http://freegeoip.net/xml/" + addr
    #print ("request url is " + url)
    #reply = urllib.request.urlopen(url) ->python3.5 methods
    reply = urllib.request.urlopen(url)
    contents = reply.read()
    #decode the receiving data and parse it to find the latitude and longitude
    contents = contents.decode("utf-8")
    lines = contents.splitlines()
    latitude = 0
    longitude = 0
    for line in lines:
        a = line.find("<Latitude>") + 1
        if a:
            latitude = line[(a+len("<Latitude>")-1) : (len(line) - len("</Latitude>"))]
            #print (latitude)

        a = line.find("<Longitude>") + 1
        if a:
            longitude = line[(a+len("<Longitude>")-1) :(len(line) - len("</Longitude>"))]
            #print (longitude)
    return latitude, longitude

def caldist(mylatitude, mylongitude, destlatitude, destlongitude):
    #calculating the geographical distance using the latiude and longitude of both my computer and destination
    #the earth is abstracted in to a sphere
    distance = 0
    earthR = 6371.0 #the radius of earth is abstracted t o 6371 kilometers in this program
    myla = math.radians(mylatitude)
    mylo = math.radians(mylongitude)
    destla = math.radians(destlatitude)
    destlo = math.radians(destlongitude)
    deltaphi = myla - destla
    deltalambda = mylo - destlo
    phim = (myla + destla)/2
    distance = earthR*math.sqrt(math.pow(deltaphi,2) + (math.cos(phim)*math.pow(deltalambda,2)))
    return distance


dist_threshold = 0.1

multicast_group = '224.3.29.71'
server_address = ('', 10000)

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

print('sending acknowledgement to', ('224.3.29.71', 10000))
message = 'ack'
sock.sendto(message.encode('UTF-8'), ('224.3.29.71', 10000))

# Receive/respond loop
while True:
    print('waiting to receive message')
    data, address = sock.recvfrom(1024)

    try:
        data = json.loads(data)
        print('received %s bytes from %s' % (data, address))
    except:
        data = data.decode()
        print('received %s bytes from %s' % (data, address))
        print(". . .")
    
    # if (address != socket.gethostbyname(socket.gethostname())):
    if(data == 'ack'):
        for message in messages:
            distance = geoDistance(message['src_address'])
            if(distance >= dist_threshold):
                print('sending message to', address)
                sock.sendto(json.dumps(message).encode('UTF-8'), address)
            else:
                messages.remove(message)
    else:
        messages.append(data)

        try:
            if(data['uuid'] not in uuids):
                uuids.append(data['uuid'])
                print(data)
        except:
            print(data)