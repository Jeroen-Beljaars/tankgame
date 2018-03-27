import socket
import threading
import json
import time
# [i] is ene informatie bericht
# [!] is een error of een waarschuwing
# [+] Is een nieuwe connectie 
# [-] Is een afgesloten connectie

class Server:
    def __init__(self):
        self.bind_ip = "192.168.178.88"
        self.bind_port = 9999

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.bind_ip, self.bind_port))
        self.server.listen(5)
        #self.server.setblocking(False)
        # Store the user_addresses here
        self.user_addresses = {}

        self.client_id = 1

        print("[i] Started listening on {}:{}".format(self.bind_ip, self.bind_port))

        self.newcomer = ""

        listen = threading.Thread(self.listener())
        listen.start()

        ping_clients = threading.Thread(target=self.ping_clients)
        ping_clients.start()


    def handle_client(self, client_socket):
        while True:
            try:
                request = client_socket.recv(1024)
                if request == b'\x1a' or request == b'':
                    self.user_addresses.pop("{}:{}".format(client_socket.getpeername()[0], client_socket.getpeername()[1]))
                    print("[-] Client {}:{} disconnected".format(client_socket.getpeername()[0],client_socket.getpeername()[1]))
                else:
                    print("Client: {}".format(request))

                try:
                    data = json.loads(request.decode())
                    if 'key_press' in data.keys():
                        self.broadcast_message(request)
                    elif 'init_connection' in data.keys():
                        self.newcomer.sendall(request)
                except:
                    pass

            except socket.error:
                try:
                    print("[-] Client {} disconnected".format(client_socket.getpeername()[0], client_socket.getpeername()[1]))
                    self.user_addresses.pop("{}:{}".format(client_socket.getpeername()[0], client_socket.getpeername()[1]))
                except:
                    break
                    pass

    def listener(self):
        while True:
            client, addr = self.server.accept()

           #  if addr[0] in self.user_addresses.keys():
           #     print("[!] Refused connection. User allready in game.")
           #     client.close()
           # else:
            print("[+] Accepted connection from {}:{}".format(addr[0], addr[1]))
            print("[+] Establishing a connection form: {}:{}".format(addr[0], addr[1]))

            self.user_addresses["{}:{}".format(addr[0], addr[1])] = client

            self.newcomer = client

            if len(self.user_addresses.values()) > 1:
                for returner in self.user_addresses.values():
                    try:
                        returner.sendall(b'send all positions')
                    except socket.error:
                        returner.close()
                        self.user_addresses.pop("{}:{}".format(returner.getpeername[0], returner.getpeername[1]))
                    break

            self.broadcast_new_connection("{}:{}".format(addr[0], addr[1]))

            client_handler = threading.Thread(target=self.handle_client,args=(client,))
            client_handler.start()

    def broadcast_new_connection(self, ip):
        new_connection = {
            'new-connection': {
                'ip': ip,
                'object': 'Tank'
            }
        }

        for client in self.user_addresses.values():
            client.sendall(json.dumps(new_connection).encode())

    def broadcast_message(self, json):
        for client in self.user_addresses.values():
            client.sendall(json)

    def ping_clients(self):
        while True:
            print("ping")
            for client in self.user_addresses:
                try:
                    client.sendall(b"ping")
                    client.recv(1024)
                except socket.error:
                    client.close()
                    self.user_addresses.pop("{}:{}".format())
                    print("[-] Disconnected user: {} non-replying client".format(client.getpeername()))
                    break
            time.sleep(5)

server = Server()
