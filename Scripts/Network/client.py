import socket
import threading
from bge import logic, events
from mathutils import Vector, Euler
import json
import traceback
import re
import requests

def keyDown(key_code=events.WKEY, status=logic.KX_INPUT_ACTIVE):
    """
    This method checks if the key (key_code) is active
    i.e. keyDown(events.WKEY) checks if the w_key is being pressed
    """
    if logic.keyboard.events[key_code] == status:
        return True
    return False

class Client:
    def __init__(self):
        """" Initialize the client """

        # Set this to True if you run it locally and to False if you run it on a server
        self.local = False

        # Here we store what player belongs to this instance of the client
        self.user_initialized = False;
        self.user = []

        # The IP & Port of the server
        self.server_ip = "oege.ie.hva.nl"
        self.server_port = 9999

        # Connect to the server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.server_ip, self.server_port))
        print("[i] connected to server")

        self.server.setblocking(False)

        if not self.local:
            self.ip = requests.get("http://ipecho.net/plain?").text
        else:
            self.ip = self.server.getsockname()[0]

        self.port = self.server.getsockname()[1]
        # Here we store the player objects (the tanks)
        # So we can move it in the scene and get the world positions
        self.players = {}

        self.oldpos = []

    def worldpos(self):
        """" Send the worldposition of the player object to the server """
        try:
            player = self.players["{}:{}".format(self.ip, self.port)]
            pos = [list(player.worldPosition), player.localOrientation.to_euler()[2]]
            if self.oldpos != pos:
                key_stat = {
                    'position': {
                        'coordinates': pos,
                        'ip': "{}:{}".format(self.ip, self.port)
                    }
                }
                self.oldpos = [list(player.worldPosition), player.localOrientation.to_euler()[2]]
                self.server.sendall(json.dumps(key_stat).encode())
        except:
            print("erro")
            # not initialized yet

    def movement(self, player):
        # Basic movement (forward, backwards, left, right)
        w_key = keyDown(events.WKEY)
        s_key = keyDown(events.SKEY)
        a_key = keyDown(events.AKEY)
        d_key = keyDown(events.DKEY)

        if w_key:
            player.applyMovement((0.1, 0, 0), True)
        elif s_key:
            player.applyMovement((-0.1, 0, 0), True)

        if a_key:
            player.applyRotation((0, 0, 0.05), False)
        elif d_key:
            player.applyRotation((0, 0, -0.05), False)

    def recieve(self):
        """"
        Recieve all the packets from the server.
        Check what kind of packet it is: movement? new connection?
        and handle the packet
        """
        try:
            # Listen for incoming packets
            data = self.server.recv(10024)
            try:
                # Sometimes the packets come in so fast that it is "merged together" (First json, second json)
                # We then have to recognize this so we can decode every json and place it in a queue
                state = re.split('(\{.*?\})(?= *\{)', data.decode())
                accumulator = ''
                res = []
                for subs in state:
                    accumulator += subs
                    try:
                        res.append(json.loads(accumulator))
                        accumulator = ''
                    except:
                        pass
            except:
                pass
                print("Something went wrong while decoding the json")
            else:
                # For every json check what kind of dict it is
                # If it found the type handle the packet
                for packet in res:
                    if 'new-connection' in packet.keys():
                        """"
                        A new client has connected to the server
                        We spawn it on the client's game so he can see it too
                        We the player under the IP of the new client so we can apply movement on it later
                        """

                        # Ip of the new client
                        ip = packet['new-connection']['ip']

                        # What is the name of the object the client has?
                        # Might be usefull for upgrades ect..
                        object = packet['new-connection']['object']

                        # Get the current scene and spawn the client in the spawner
                        scene = logic.getCurrentScene()
                        spawner = scene.objects["Spawner"]
                        player = scene.addObject(object, spawner)

                        # Add the ip to the player object
                        player["ip"] = ip
                        self.players[ip] = player

                        # If it is the first time a user is "intitialized" then we know that this is
                        # the user that belongs to this client. So we store the object
                        if self.user_initialized == False:
                            self.local_user = player
                            self.user_initialized = True


                    if 'init_connection' in packet:
                        """" 
                        if a user connects to the server and there are allready other players inside the game
                        then we need to get the information about the other objects so we can spawn them in ect..
                        """
                        for event in packet['init_connection']['objects']:
                            scene = logic.getCurrentScene()
                            spawner = scene.objects["Spawner"]
                            player = scene.addObject('Tank', spawner)
                            player['ip'] = event
                            self.players[event] = player

                            # Handle the rotation
                            # We use Eueler for this (the last number handles the Z rotation)
                            player.localOrientation = [0, 0, packet['init_connection']['objects'][event][1]]

                            # Change the players position to the given position
                            # We us a vecor for this
                            player.worldPosition = Vector(packet['init_connection']['objects'][event][0])

                    if 'position' in packet.keys():
                        """" 
                        These packets contain the position (worldlocation & rotation) of a specific player
                        if the ip in the packet is not equal to the clients IP then apply the movement
                        (otherwise this will override the movement and the player would be stuck on one position)
                        """
                        if self.user_initialized and packet['position']['ip'] \
                                != "{}:{}".format(self.ip, self.port):
                            try:
                                # Get the object that belongs to that ip
                                instance = self.players[packet['position']['ip']]

                                # Handle the rotation
                                instance.localOrientation = [0, 0, packet['position']['coordinates'][1]]

                                # Handle the movement
                                instance.worldPosition = Vector(packet['position']['coordinates'][0])
                            except:
                                # NOTE: it's possible that this packet came in before we initialized the objects
                                # so it can probably not find the right object. So no worries about this error
                                print("Something went wrong handling the position. Line: 150")

                    if 'send all positions' in packet.keys():
                        """" 
                        If the server gets a new connection and there are allready players in game
                        then it will request the info about the other objects.
                        so when the client gets this packet it sends all the clients back
                        """
                        scene = logic.getCurrentScene()
                        players = {
                            gobj["ip"]: [list(gobj.worldPosition), gobj.localOrientation.to_euler()[2]] \
                            for gobj in scene.objects \
                            if gobj.name == "Tank"
                        }

                        position = {
                            'init_connection': {
                                'objects': players
                            }
                        }
                        self.server.sendall(json.dumps(position).encode())
        except socket.error:
            pass

client = Client()

def movement():
    if client.user_initialized == True:
        client.movement(client.local_user)

def sendworldpos():
    client.worldpos()

def recieve():
    client.recieve()