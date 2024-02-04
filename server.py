import socket
from  threading import Thread
import time
import os

#For FTP Server
#pip install pyftpdlib < this should be installed
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

IP_ADDRESS = '127.0.0.1'
PORT = 8080
SERVER = None
BUFFER_SIZE = 4096
clients = {}

# Boilerplate Code Start
is_dir_exists = os.path.isdir('shared_files')
if(not is_dir_exists):
    os.makedirs('shared_files')

# Boilerplate Code End

def removeClient(client_name):
    try:
        if client_name in clients:
            del clients[client_name]
    except KeyError:
        pass


def sendTextMessage(client_name, message):
    global clients

    other_client_name = clients[client_name]["connected_with"]
    other_client_socket = clients[other_client_name]["client"]
    final_message = client_name + " > " + message
    other_client_socket.send(final_message.encode())

def handleErrorMessage(client):
    message = '''
    You need to connect with one of the client first before sending any message.
    Click on Refresh to see all available users.'''
    client.send(message.encode())


# SA Boilerplate Code
def declineAccess(client_name):
    global clients

    other_client_name = clients[client_name]["connected_with"]
    other_client_socket = clients[other_client_name]["client"]
    msg = f"Oops!!! {client_name} decline your request..."
    other_client_socket.send(msg.encode())

# SA Boilerplate Code
def grantAccess(client_name):
    global clients

    other_client_name = clients[client_name]["connected_with"]
    other_client_socket = clients[other_client_name]["client"]
    msg = "access granted"
    other_client_socket.send(msg.encode())

# Teacher Activity
def handleSendFile(client_name, file_name, file_size):
    global clients

    clients[client_name]["file_name"] = file_name
    clients[client_name]["file_size"] = file_size
    other_client_name = clients[client_name]["connected_with"]
    other_client_socket = clients[other_client_name]["client"]
    msg = f"\n{client_name} want to send {file_name} file with size {file_size} bytes. Do you want to download ? Y/N "
    other_client_socket.send(msg.encode())
    time.sleep(1)
    msgdown=f"Download:{file_name}"
    other_client_socket.send(msgdown.encode())



def disconnectWithClient(message, client, client_name):
    global clients

    entered_client_name = message[11:].strip()
    if(entered_client_name in clients):
        clients[entered_client_name]["connected_with"] = ""
        clients[client_name]["connected_with"]  = ""

        other_client_socket = clients[entered_client_name]["client"]

        greet_message = f"Hello, {entered_client_name} you are successfully disconnected with {client_name} !!!"
        other_client_socket.send(greet_message.encode())

        msg = f"You are successfully disconnected with {entered_client_name}"
        client.send(msg.encode())



def handleClientConnection(message, client, client_name):
    global clients

    entered_client_name = message[8:].strip()
    if(entered_client_name in clients):
        if(not clients[client_name]["connected_with"]):
            clients[entered_client_name]["connected_with"] = client_name
            clients[client_name]["connected_with"]  = entered_client_name

            other_client_socket = clients[entered_client_name]["client"]

            greet_message = f"Hello, {entered_client_name} {client_name} connected with you !!!"
            other_client_socket.send(greet_message.encode())

            msg = f"You are successfully connected with {entered_client_name}"
            client.send(msg.encode())
        else:
            other_client_name = clients[client_name]["connected_with"]
            msg = f"You are already connected with {other_client_name}"
            client.send(msg.encode())


def handleShowList(client):
    global clients

    counter = 0
    for c in clients:
        counter +=1
        client_address = clients[c]["address"][0]
        connected_with = clients[c]["connected_with"]
        message =""
        if(connected_with):
            message = f"{counter},{c},{client_address}, connected with {connected_with},tiul,\n"
        else:
            message = f"{counter},{c},{client_address}, Available,tiul,\n"
        client.send(message.encode())
        time.sleep(1)


# Teacher Activity Code Start
def handleMessges(client, message, client_name):
    if(message == 'show list'):
        handleShowList(client)
    elif(message[:7] == 'connect'):
        handleClientConnection(message, client, client_name)
    elif(message[:10] == 'disconnect'):
        disconnectWithClient(message, client, client_name)
    elif(message[:4] == "send"):
        file_name = message.split(" ")[1]
        file_size  = int(message.split(" ")[2])
        handleSendFile(client_name, file_name, file_size)
        print(client_name+" "+file_name+" "+file_size)
# Teacher Activity Code End

    # Student Activity 1 Boilerplate Code Start
    elif(message == "y" or message == "yes"):
        grantAccess(client_name)
    elif(message == "n" or message == "no"):
        declineAccess(client_name)
    # Student Activity Boilerplate Code End

    else:
        connected = clients[client_name]["connected_with"]
        if(connected):
            sendTextMessage(client_name, message)
        else:
            handleErrorMessage(client)

def handleClient(client, client_name):
    global clients
    global BUFFER_SIZE
    global SERVER

    # Sending welcome message
    banner1 = "Welcome, You are now connected to Server!\nClick on Refresh to see all available users.\nSelect the user and click on Connect to start chatting."
    client.send(banner1.encode())

    while True:
        try:
            BUFFER_SIZE = clients[client_name]["file_size"]
            chunk = client.recv(BUFFER_SIZE)
            message = chunk.decode().strip().lower()
            if(message):
                handleMessges(client, message, client_name)
            else:
                removeClient(client_name)
        except:
            pass

def acceptConnections():
    global SERVER
    global clients

    while True:
        client, addr = SERVER.accept()
        client_name = client.recv(4096).decode().lower()
        clients[client_name] = {
                "client"         : client,
                "address"        : addr,
                "connected_with" : "",
                "file_name"      : "",
                "file_size"      : 4096
            }

        print(f"Connection established with {client_name} : {addr}")

        thread = Thread(target = handleClient, args=(client,client_name,))
        thread.start()

def setup():
    print("\n\t\t\t\t\t\tIP MESSENGER\n")

    # Getting global values
    global PORT
    global IP_ADDRESS
    global SERVER


    SERVER  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    SERVER.bind((IP_ADDRESS, PORT))

    # Listening incomming connections
    SERVER.listen(100)

    print("\t\t\t\tSERVER IS WAITING FOR INCOMMING CONNECTIONS...")
    print("\n")

    acceptConnections()

def ftp():
    global IP_ADDRESS

    authorizer = DummyAuthorizer()
    authorizer.add_user("lftpd","lftpd",".",perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer

    ftp_server = FTPServer((IP_ADDRESS,21),handler)
    ftp_server.serve_forever()

setup_thread = Thread(target=setup)           #receiving multiple messages
setup_thread.start()

ftp_thread = Thread(target=ftp)               #receiving multiple messages
ftp_thread.start()
