from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread
import time
import json

class Serwer:
    def __init__(self):
        with open('config.json') as f:
            self.config = json.load(f)
        # initialize server
        self.host = self.config["ip"]
        self.port = self.config["port"]
        self.bufforSize = 1024
        self.addres = (self.HOST, self.PORT)

        self.addresses = {}
        self.serwer = socket(AF_INET, SOCK_STREAM)
        self.serwer.bind(self.addres)
        self.serwer.listen(5)
        print("Waiting for connection...")
        Thread(target = self.accept()).start()

    def accept(self):
        # wait for first player
        client1, client_address1 = self.serwer.accept()
        print("%s:%s has connected." % client_address1)
        name1, apple = client1.recv(self.BUFSIZ).decode("utf8").split(";")
        client1.send(bytes("Hello", "utf8"))

        # wait for second player
        client2, client_address2 = self.serwer.accept()
        print("%s:%s has connected." % client_address2)
        name2, _ = client2.recv(self.BUFSIZ).decode("utf8").split(";")
        client2.send(bytes("start", "utf8"))
        client1.send(bytes("start", "utf8"))
        time.sleep(0.5)
        client2.send(bytes(f"2;{name1};{apple}", "utf8"))
        client1.send(bytes(f"1;{name2};{apple}", "utf8"))

        # create players threads
        Thread(target=self.recvClient, args=(client1, client2,)).start()
        Thread(target=self.recvClient, args=(client2, client1,)).start()

    def recvClient(self, client, enemy):
        while True:
            msg = client.recv(self.BUFSIZ)
            enemy.send(msg)


serwer = Serwer()
