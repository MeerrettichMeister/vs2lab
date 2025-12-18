import time

import zmq

import constPipe

context = zmq.Context()
push_socket1 = context.socket(zmq.PUSH)

mapper1 = "tcp://" + constPipe.SRC1 + ":" + constPipe.PORT1

push_socket1.bind(mapper1)


time.sleep(2)

with open("test.txt") as f: file = f.readlines()

for i, line in enumerate(file):
    push_socket1.send_string(line)
