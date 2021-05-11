'''
Client to time interactions with opc ua servers
'''

import sys, os, datetime
sys.path.insert(0, "..")
import asyncio
import logging
from asyncua import Client, Node, ua
import time
import numpy as np
import pandas as pd

# create directory for test data
data_path = "./timing/"
if not os.path.exists(data_path):
    os.mkdir(data_path)


logging.basicConfig(level=logging.INFO) # logging.INFO as default
_logger = logging.getLogger(__name__) #'asyncua')


async def time_write(var, cycles):
    """
        time the delay of write operations and return timing_vec with len(cycles)
    """
    timing_vec = np.zeros(cycles)
    for i in range(cycles):
        t1 = time.perf_counter_ns()
        await var.write_value(0.0)
        t2 = time.perf_counter_ns()
        timing_vec[i] = t2-t1
    return timing_vec


async def main(host='localhost'):
    
    server_endpoint = f"opc.tcp://{host}:4840/server_example/"
    client = Client(url=server_endpoint)
    not_connected = True
    while not_connected:
        try:
            async with client:
                not_connected = False
                idx = await client.get_namespace_index(uri="example-uri.edu")
                # get motor object, here path from root folder
                motor_obj = await client.nodes.root.get_child(["0:Objects", f"{idx}:Motor"])
                # get motor variables
                motor_rpm = await client.nodes.objects.get_child(path=[f"{idx}:Motor", f"{idx}:RPM"])
                motor_inp = await client.nodes.objects.get_child(path=[f"{idx}:Motor", f"{idx}:Input"])

                # time write operations
                _logger.info('time write operations')
                write_vec = await time_write(motor_rpm, 10000)
                df = pd.DataFrame({"write_value":write_vec})
                _logger.info(f'TIMING for write value:\tmean {df["write_value"].mean()}\tmeadian {df["write_value"].median()}')
                now = datetime.datetime.now()
                df.to_csv(f'{data_path}{now.year}_{now.month}_{now.day}_{now.minute}_{now.second}')

        except asyncio.exceptions.TimeoutError:
            _logger.warning(f'Connection failed. Connecting again to {server_endpoint}')
            continue


if __name__ == "__main__":
    if len(sys.argv)>1:
        host = sys.argv[1]
    else:
        host='192.168.0.183'
    asyncio.run(main(host))
    