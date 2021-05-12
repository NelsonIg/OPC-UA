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

async def time_method(var, idx, cycles, delay=0):
    """
        time the daly of method calls and return timing_vec of len(cycles)
    """
    timing_vec = np.zeros(cycles)
    for i in range(cycles):
        t1 = time.perf_counter_ns()
        await var.call_method(f"{idx}:stop_motor")
        t2 = time.perf_counter_ns()
        timing_vec[i] = t2-t1
        if delay >0:
            await asyncio.sleep(delay)
    return timing_vec

async def time_write(var, cycles, delay=0):
    """
        time the delay of write operations and return timing_vec with len(cycles)
    """
    timing_vec = np.zeros(cycles)
    for i in range(cycles):
        t1 = time.perf_counter_ns()
        await var.write_value(0.0)
        t2 = time.perf_counter_ns()
        timing_vec[i] = t2-t1
        if delay >0:
            await asyncio.sleep(delay)
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
                cycles=10**3
                delay = 0

                _logger.info('start timing of write operations')
                t1 = time.perf_counter()
                write_vec = await time_write(motor_rpm, cycles, delay)
                t2 = time.perf_counter()
                _logger.info(f'finished timing of write operations: {t2-t1}s')
                _logger.info('start timing of method calls')
                t1 = time.perf_counter()
                method_vec = await time_method(motor_obj, idx, cycles, delay)
                t2 = time.perf_counter()
                _logger.info(f'finished timing of method calls: {t2-t1}s')

                df = pd.DataFrame({"write_value":write_vec, "method_call": method_vec})
                _logger.info(f'TIMING for write_value:\tmean {df["write_value"].mean()}ns\tmeadian {df["write_value"].median()}ns')
                _logger.info(f'TIMING for method_call:\tmean {df["method_call"].mean()}ns\tmeadian {df["method_call"].median()}ns')
                # store data
                now = datetime.datetime.now()
                filename = f'{data_path}timed_cylces_{cycles}_delay_{delay}.csv'
                df.to_csv(filename)

        except asyncio.exceptions.TimeoutError:
            _logger.warning(f'Connection failed. Connecting again to {server_endpoint}')
            continue


if __name__ == "__main__":
    if len(sys.argv)>1:
        host = sys.argv[1]
    else:
        host='192.168.0.183'
    asyncio.run(main(host))
    