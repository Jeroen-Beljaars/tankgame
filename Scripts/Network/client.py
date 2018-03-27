import socket
import threading
from bge import logic, events
from mathutils import Vector, Euler
import json
import traceback
import re

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
        self.user_initialized = False;
        self.user = []

        self.server_ip = "192.168.178.88"
        self.server_port = 9999

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.server.setblocking(False)
        self.server.connect((self.server_ip, self.server_port))
        print("[i] connected to server")

        self.player_list = {}
        self.players = {}

        reciever = threading.Thread(target=self.recieve)
        reciever.start()

        self.player = ""

    def worldpos(self):
        try:
            player = self.players["{}:{}".format(self.server.getsockname()[0], self.server.getsockname()[1])]
            key_stat = {
                'key_press': {
                    'key_codes': [list(player.worldPosition), player.localOrientation.to_euler()[2]],
                    'ip': "{}:{}".format(self.server.getsockname()[0], self.server.getsockname()[1])
                }
            }
            self.server.sendall(json.dumps(key_stat).encode())
        except:
            pass
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
        while True:
            try:
                data = self.server.recv(10024)
                print(data)
                try:
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
                    print("smth went wrong lel")
                else:
                    for state in res:
                        if 'new-connection' in state.keys():
                            ip = state['new-connection']['ip']
                            object = state['new-connection']['object']

                            scene = logic.getCurrentScene()
                            spawner = scene.objects["Spawner"]
                            player = scene.addObject(object, spawner)
                            player["ip"] = ip
                            self.players[ip] = player

                            if self.user_initialized == False:
                                self.local_user = player
                                self.user_initialized = True


                        if 'init_connection' in state:
                            for event in state['init_connection']['objects']:
                                scene = logic.getCurrentScene()
                                spawner = scene.objects["Spawner"]
                                player = scene.addObject('Tank', spawner)
                                player['ip'] = event
                                self.players[event] = player

                                # Handle the rotation
                                player.localOrientation = [0, 0, state['init_connection']['objects'][event][1]]

                                # Handle the movement
                                player.worldPosition = Vector(state['init_connection']['objects'][event][0])

                        if 'key_press' in state.keys():
                            if self.user_initialized and state['key_press']['ip'] != "{}:{}".format(self.server.getsockname()[0], self.server.getsockname()[1]):
                                try:
                                    instance = self.players[state['key_press']['ip']]
                                    # Handle the rotation
                                    instance.localOrientation = [0, 0, state['key_press']['key_codes'][1]]

                                    # Handle the movement
                                    instance.worldPosition = Vector(state['key_press']['key_codes'][0])
                                except:
                                    pass
                                    #not initialized yet
                        if 'send all positions' in state.keys():
                            scene = logic.getCurrentScene()
                            state = {
                                gobj["ip"]: [list(gobj.worldPosition), gobj.localOrientation.to_euler()[2]] \
                                for gobj in scene.objects \
                                if gobj.name == "Tank"
                            }

                            position = {
                                'init_connection': {
                                    'objects': state
                                }
                            }
                            self.server.sendall(json.dumps(position).encode())
            except socket.error:
                print(">>>STACKTRACE<<<")
                traceback.print_exc()
                print("<<<STACKTRACE>>>")

client = Client()

def movement():
    if client.user_initialized == True:
        client.movement(client.local_user)

def sendworldpos():
    client.worldpos()