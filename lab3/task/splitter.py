import sys
import pickle
import time

import zmq

import constPipe

me = str(sys.argv[1])

context = zmq.Context()
push_socket1 = context.socket(zmq.PUSH)  # create a push socket
push_socket2 = context.socket(zmq.PUSH)  # create a push socket
push_socket3 = context.socket(zmq.PUSH)  # create a push socket

mapper1 = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT1  # how and where to connect
mapper2 = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT2
mapper3 = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT3

push_socket1.bind(mapper1)  # bind socket to address
push_socket2.bind(mapper2) 
push_socket3.bind(mapper3)

sockets = [push_socket1, push_socket2, push_socket3]

time.sleep(2)

with open("text.txt") as f: file = f.readlines()

for i, line in enumerate(file):
    sockets[i % 3].send_string(line)
