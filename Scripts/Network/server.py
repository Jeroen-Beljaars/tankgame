import socket
import threading
import json
import time
import re
# [i] is ene informatie bericht
# [!] is een error of een waarschuwing
# [+] Is een nieuwe connectie 
# [-] Is een afgesloten connectie


class Server:
    def __init__(self):
        """ Initialize the server """

        # The ip of the machine where the server is running on
        self.bind_ip = "oege.ie.hva.nl"

        # The port that we use for the server
        self.bind_port = 9999

        #
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.bind_ip, self.bind_port))
        self.server.listen(5)
        # self.server.setblocking(False)

        # Store the user_addresses here
        self.user_addresses = {}

        self.client_id = 1

        print("[i] Started listening on {}:{}".format(self.bind_ip, self.bind_port))

        self.newcomer = ""

        listen = threading.Thread(self.listener())
        listen.start()

    def handle_client(self, client_socket):
        """
        Every client has an own handler
        this method listens for incoming messages from a specific client
        """
        while True:
            try:
                # listen for packets
                request = client_socket.recv(10024)

                # The client sometimes sends this if it disconnects.
                # If we recieve this then close the connection and remove the user from the list
                if request == b'\x1a' or request == b'':
                    self.user_addresses.pop("{}:{}".format(client_socket.getpeername()[0], client_socket.getpeername()[1]))
                    print("[-] Client {}:{} disconnected".format(client_socket.getpeername()[0],client_socket.getpeername()[1]))
                else:
                    pass
                    # print the recieved message
                    # print("Client: {}".format(request))

                try:
                    # Decode the json and check if it matches any of the keys below
                    data = json.loads(request.decode())
                    splitter = request.decode()

                    state = re.split('(\{.*?\})(?= *\{)', splitter)
                    accumulator = ''
                    res = []
                    for subs in state:
                        accumulator += subs
                        try:
                            res.append(json.loads(accumulator))
                            accumulator = ''
                        except:
                            pass
                    for packet in res:
                        if 'position' in packet.keys():
                            self.broadcast_message(json.dumps(packet).encode())
                        elif 'init_connection' in packet.keys():
                            print(packet)
                            self.newcomer.sendall(json.dumps(packet).encode())
                except:
                    pass

            except socket.error:
                # Socket error usally means that the client is not connected anymore
                # Disconnect it
                try:
                    self.user_addresses.pop("{}:{}".format(client_socket.getpeername()[0], client_socket.getpeername()[1]))
                    print("[-] Client {} disconnected".format(client_socket.getpeername()[0], client_socket.getpeername()[1]))
                    break
                except:
                    # If disconnecting failed then the user is allready disconnected elsewhere
                    break

    def listener(self):
        """" Listen for new incomming connections """
        while True:
            client, addr = self.server.accept()

            # if addr[0] in self.user_addresses.keys():
            #    print("[!] Refused connection. User allready in game.")
            #    client.close()
            # else:

            print("[+] Accepted connection from {}:{}".format(addr[0], addr[1]))
            print("[+] Establishing a connection form: {}:{}".format(addr[0], addr[1]))

            # add the user to the client list
            self.user_addresses["{}:{}".format(addr[0], addr[1])] = client

            # save the latest newcomer so we can send the init_connection packet to the client later
            self.newcomer = client

            # if there are all ready players connected request all the info from the player objects
            # from the first player in the list
            if len(self.user_addresses.values()) > 1:
                for returner in self.user_addresses.values():
                    try:
                        returner.sendall(json.dumps({"send all positions": "please?"}).encode())
                    except socket.error:
                        returner.close()
                        self.user_addresses.pop("{}:{}".format(returner.getpeername()[0], returner.getpeername()[1]))
                    break

            self.broadcast_new_connection("{}:{}".format(addr[0], addr[1]))

            # start the client handler
            client_handler = threading.Thread(target=self.handle_client,args=(client,))
            client_handler.start()

    def broadcast_new_connection(self, ip):
        """" If a player joins the game then broadcast it to all the clients """
        new_connection = {
            'new-connection': {
                'ip': ip,
                'object': 'Tank'
            }
        }

        for client in self.user_addresses.values():
            client.sendall(json.dumps(new_connection).encode())

    def broadcast_message(self, packet):
        """" Broadcast the message to all the clients """
        for client in self.user_addresses.values():
            client.sendall(packet)

    def ping_clients(self):
        """" This pings the clients to check if they are still active """
        while True:
            print("ping")
            for client in self.user_addresses:
                try:
                    client.sendall(b"ping")
                except socket.error:
                    client.close()
                    self.user_addresses.pop("{}:{}".format())
                    print("[-] Disconnected user: {} non-replying client".format(client.getpeername()))
                    break
            time.sleep(5)

server = Server()
