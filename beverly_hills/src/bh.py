import time 
import json
import socket
import os
from threading import Thread
import asyncio
from autobahn.asyncio.websocket import WebSocketServerFactory
from server import BeverlyWebSocketProtocol

from client import (
    startClient,
    readData,
    readDataServer
)
from data_engine import DataEngine
from vars import (
    containersToId,
    idToContainer
)

class BeverlyHills():
    def __init__(self):
        #initialize all data structures
        
        self.coins = []
        self.connections = dict()
        self.numClients = 0
        
        self.consumerConnect()
        self.pmConnect()

        self.data_engine = DataEngine(self.coins)

    def pmConnect(self):
        conn = None
        print("Connecting to Portfolio Manager")
        while True:
            print("Trying to connect", flush=True)
            try:
                conn = startClient('portfolio_manager', os.environ["PM_PORT"])
                break
            except Exception as e:
                print(e)
                time.sleep(5)

        self.connections['portfolio_manager'] = conn
        while True:
            msg = readData(conn, 'portfolio_manager', os.environ["PM_PORT"])
            if msg["type"] == "init":
                print("Recieved init message ")
                break
                


    def consumerConnect(self):
        conn = None
        print("Connecting to Data Consumer")
        while True:
            print("Trying to connect", flush=True)
            try:
                conn = startClient('main_data_consumer', os.environ["DATAPORT"])
                break
            except Exception as e:
                print(e)
                time.sleep(5)

        self.connections['main_data_consumer'] = conn
        coins = ""
        while True:
            #change this to something else 
            rawMsg = {'type': 'coins', 'msg':'', 'src':containersToId['beverly_hills'], 'dest':containersToId['main_data_consumer']}
            conn.send(json.dumps(rawMsg).encode('utf-8'))
            coins = readData(conn, 'main_data_consumer', os.environ["DATAPORT"])
            if len(coins) > 0:
                break
            if coins["type"] == "coins":
                coins = json.loads(coins["msg"])
            else:
                raise Exception("Not sending coins back when it should")
        print("Received coins from data consumer")
        coin_msg = json.loads(coins)
        self.coins = coin_msg["msg"]
    
    def compute(self):
        
            

    def startServer(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        socketServer = WebSocketServerFactory()
        socketServer.protocol = BeverlyWebSocketProtocol
        
        coro = loop.create_server(socketServer, '0.0.0.0', int(os.environ["SERVERPORT"]))
        server = loop.run_until_complete(coro)

        loop.run_forever()

    def loop(self):
        #split off two threads, one for starting server and handling connections.
        #   wait on data from dc and compute
        serverThread = Thread(target=self.startServer)
        dataThread = Thread(target=self.compute)

        serverThread.start()
        dataThread.start()

def pingFrontend(conn):
    while True:
        conn.sendall(bytes(1,encoding='utf-8'))
        time.sleep(2)