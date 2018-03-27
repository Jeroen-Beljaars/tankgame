import socket
import threading
from bge import logic
from mathutils import Vector, Euler
import json
import traceback

class RemoteKeyboard:
    def __init__(self):
        self.key_stat = {}

    def updateState(self, list_key_stat):
        for key, stat in list_key_stat:
            self.key_stat[key] = stat

    def keyDown(self, key_code, status=logic.KX_INPUT_JUST_ACTIVATED):
        if key_code in self.key_stat:
            if self.key_stat[key_code] == status:
                return True
        return False


class User:
    def __init__(self, addr):
        # The remote keyboard instance for the user.
        self.addr = addr
        self.keyboard = RemoteKeyboard()

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

        reciever = threading.Thread(target=self.recieve)
        reciever.start()

        self.main = self.state_loop

    def state_loop(self):
        self.send()

    def send(self):
        """
        Send the state (keycodes) to the server so it knows what to do
        """
        key_stat = {
            'key_press': {
                'key_codes': [],
                'ip': "{}:{}".format(self.server.getsockname()[0],self.server.getsockname()[1])
            }
        }
        keyboard_events = logic.keyboard.events
        for event in keyboard_events:
            status = keyboard_events[event]
            if status in (logic.KX_INPUT_JUST_ACTIVATED,
                          logic.KX_INPUT_JUST_RELEASED):
                key_stat['key_press']['key_codes'].append((event, status))
        if len(key_stat['key_press']['key_codes']):
            self.server.sendall(json.dumps(key_stat).encode())

    def recieve(self):
        while True:
            try:
                data = self.server.recv(1024)

                try:
                    state = json.loads(data.decode())
                except:
                    state = data
                    if 'send all positions' in state.decode():
                        scene = logic.getCurrentScene()
                        state = {
                            gobj["user"].addr: [list(gobj.worldPosition), gobj.localOrientation.to_euler()[2]] \
                            for gobj in scene.objects \
                            if gobj.name == "Tank"
                        }

                        position = {
                            'init_connection': {
                                'objects': state
                            }
                        }
                        self.server.sendall(json.dumps(position).encode())
                else:
                    if 'new-connection' in state.keys():
                        ip = state['new-connection']['ip']
                        object = state['new-connection']['object']

                        user = User(ip)
                        scene = logic.getCurrentScene()
                        spawner = scene.objects["Spawner"]
                        player = scene.addObject(object, spawner)
                        player['user'] = user
                        self.player_list[ip] = user

                    if 'init_connection' in state:
                        for event in state['init_connection']['objects']:
                            user = User(event)
                            scene = logic.getCurrentScene()
                            spawner = scene.objects["Spawner"]
                            player = scene.addObject('Tank', spawner)
                            player['user'] = user
                            self.player_list[event] = user

                            # Handle the rotation
                            player.localOrientation = [0, 0, state['init_connection']['objects'][event][1]]

                            # Handle the movement
                            player.worldPosition = Vector(state['init_connection']['objects'][event][0])

                    if 'key_press' in state.keys():
                        instance = self.player_list[state['key_press']['ip']]
                        instance.keyboard.updateState(state['key_press']['key_codes'])

            except socket.error:
                print(">>>STACKTRACE<<<")
                traceback.print_exc()
                print("<<<STACKTRACE>>>")

client = Client()
def main():
    client.main()