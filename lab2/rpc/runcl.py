import time

import rpc
import logging

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

def print_result(result):
    print("Result: {}".format(result.value))

base_list = rpc.DBList({'foo'})
cl.append('bar', base_list, print_result)
for x in range(15):
    print(x)
    time.sleep(1)


cl.stop()
