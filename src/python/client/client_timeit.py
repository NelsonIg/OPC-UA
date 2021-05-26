'''
Client to time interactions with opc ua servers
'''

import sys, os, datetime

from asyncua.common import subscription
sys.path.insert(0, "..")

import asyncio
from asyncua import Client, Node, ua
from asyncua.common.subscription import SubHandler

import time
import numpy as np
import pandas as pd
import logging
import random as rd

# create directory for test data
data_path = "./timing/"
if not os.path.exists(data_path):
    os.mkdir(data_path)


logging.basicConfig(level=logging.INFO) # logging.INFO as default
_logger = logging.getLogger(__name__) #'asyncua')


global DATA_CHANGE_RECV, sub_time_old, sub_time_new
DATA_CHANGE_RECV = False
sub_time_old, sub_time_new = None, None
class SubscriptionHandler (SubHandler):
    """
    Handle the data that received for the subscription.
    """

    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        global DATA_CHANGE_RECV, sub_time_old, sub_time_new
        sub_time_old = sub_time_new
        sub_time_new = time.perf_counter_ns()
        DATA_CHANGE_RECV = True

async def time_subscription(client, var, cycles, case, period=10, queuesize=1):
    global DATA_CHANGE_RECV, sub_time_old, sub_time_old
    # create subscription
    sub_handler = SubscriptionHandler()
    subscription = await client.create_subscription(period=period, handler=sub_handler)
    # subscribe to data change, only current data queuesize=1
    await subscription.subscribe_data_change(nodes=var, queuesize=queuesize)
    time_sleep = ((period/100)*10**-3) * 10 # sleep 10% of period [s]
    time_vec = np.zeros(cycles)
    for i in range(cycles+1):
        DATA_CHANGE_RECV = False
        await var.write_value(rd.randint(0,1000))
        while not DATA_CHANGE_RECV:
            await asyncio.sleep(time_sleep)
        if sub_time_old and sub_time_new:
            # only store vals after at least two datachange_notifications
            time_vec[i-1] = sub_time_new-sub_time_old
    subscription.delete()
    # save dataframe to csv
    df = pd.DataFrame({'datachange_notifications': time_vec, \
                        'period': np.ones(time_vec.shape)*period, \
                        'queuesize': np.ones(time_vec.shape)*queuesize})
    df.to_csv(data_path+f'{case}_subscription_cycles_{cycles}_period_{period}_queuesize_{queuesize}.csv')

        



async def time_method(var, idx, cycles, case, delay=0):
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
    df = pd.DataFrame({'method_call': timing_vec, 'delay': np.ones(timing_vec.shape)*delay})
    df.to_csv(data_path+f'{case}_method_cycles_{cycles}_delay_{delay}.csv')

async def time_write(var, cycles, case, delay=0):
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
    df = pd.DataFrame({'write_value': timing_vec, 'delay': np.ones(timing_vec.shape)*delay})
    df.to_csv(data_path+f'{case}_write_value_cycles_{cycles}_delay_{delay}.csv')


async def main(host='localhost'):
    server_endpoint = f"opc.tcp://{host}:4840"
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
                cycles=10**4
                delay = 0
                case='ether(S)-ether(C)'

                # _logger.info('start timing of write operations')
                # t1 = time.perf_counter()
                # await time_write(motor_rpm, cycles, case, delay)
                # t2 = time.perf_counter()
                # _logger.info(f'finished timing of write operations: {t2-t1}s')
                
                # _logger.info('start timing of method calls')
                # t1 = time.perf_counter()
                # await time_method(motor_obj, idx, cycles, case, delay)
                # t2 = time.perf_counter()
                # _logger.info(f'finished timing of method calls: {t2-t1}s')
                
                _logger.info('start timing datachange_notifications')
                t1 = time.perf_counter()
                await time_subscription(client, motor_rpm, cycles, case, period=10)
                t2 = time.perf_counter()
                _logger.info(f'finished timing of datachange_notifications: {t2-t1}s')

        except asyncio.exceptions.TimeoutError:
            _logger.warning(f'Connection failed. Connecting again to {server_endpoint}')
            continue


if __name__ == "__main__":
    if len(sys.argv)>1:
        host = sys.argv[1]
    else:
        host='192.168.0.183'
    asyncio.run(main(host))
 