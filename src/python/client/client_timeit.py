'''
Client to time interactions with server_timeit.py
'''

import sys, os
sys.path.insert(0, "..")


import asyncio
from asyncua import Client, Node, ua
from asyncua.common import subscription
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



global timestamp_list
timestamp_list = []
class SubscriptionHandler (SubHandler):
    """
    Handle the data that received for the subscription.
    """

    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        global timestamp_list
        timestamp_list.append(time.perf_counter_ns())


async def time_subscription(client, obj, idx, var, var_name, case, period=10, change_int=1, duration=100, queuesize=1):
    """
    period: desired period of notification messages [ms]
    change_int: interval of datachange of variable value [ms]
    duration: duration of test [sec]
    """
    global timestamp_list
    change_int_sec = change_int*10**-3
    # create subscription
    sub_handler = SubscriptionHandler()
    subscription = await client.create_subscription(period=period, handler=sub_handler)
    # subscribe to data change; only current data --> queuesize=1
    await subscription.subscribe_data_change(nodes=var, queuesize=queuesize)
    # start notification test
    await obj.call_method(f"{idx}:start_notification_test", \
                            change_int_sec, var_name)
    await asyncio.sleep(duration)
    await obj.call_method(f"{idx}:stop_notification_test")
    subscription.delete()
    # compute timedifference between notification messages
    time_vec = []
    for i in range(len(timestamp_list)-1):
        time_vec.append(timestamp_list[i+1]-timestamp_list[i])
    time_vec = np.array(time_vec)[1::]
    # save dataframe to csv
    df = pd.DataFrame({'datachange_notifications': time_vec, \
                        'period': np.ones(time_vec.shape)*period, \
                        'queuesize': np.ones(time_vec.shape)*queuesize, \
                        'change_int':  np.ones(time_vec.shape)*change_int})
    df.to_csv(data_path+f'{case}_subscription_duration_{duration}_period_{period}_changeInt_{change_int}_queuesize_{queuesize}.csv')

        



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
        time the delay of write operations and safe as csv-file
    """
    timing_vec = np.zeros(cycles)
    for i in range(cycles):
        random_value = round(rd.random(),2) # random float [0.00 - 1.00] 
        t1 = time.perf_counter_ns()
        await var.write_value(random_value)
        t2 = time.perf_counter_ns()
        timing_vec[i] = t2-t1
        if delay >0:
            await asyncio.sleep(delay)
    df = pd.DataFrame({'write_value': timing_vec, 'delay': np.ones(timing_vec.shape)*delay})
    df.to_csv(data_path+f'{case}_write_value_cycles_{cycles}_delay_{delay}.csv')


async def main(host='0.0.0.0'):
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

                cycles=10**3
                delay = 0
                case='test'

                _logger.info('start timing of write operations')
                t1 = time.perf_counter()
                await time_write(motor_rpm, cycles, case, delay)
                t2 = time.perf_counter()
                _logger.info(f'finished timing of write operations: {t2-t1}s')
                
                _logger.info('start timing of method calls')
                t1 = time.perf_counter()
                await time_method(motor_obj, idx, cycles, case, delay)
                t2 = time.perf_counter()
                _logger.info(f'finished timing of method calls: {t2-t1}s')
                
                _logger.info('start timing datachange_notifications')
                t1 = time.perf_counter()
                await time_subscription(client, obj=motor_obj, idx=idx, var=motor_rpm, \
                            var_name='RPM', case=case, period=10, change_int=1, duration=100)
                t2 = time.perf_counter()
                _logger.info(f'finished timing of datachange_notifications: {t2-t1}s')

        except asyncio.exceptions.TimeoutError:
            _logger.warning(f'Connection failed. Connecting again to {server_endpoint}')
            continue


if __name__ == "__main__":
    if len(sys.argv)>1:
        # arguments passed to script
        # accepted options: -h/--host
        # syntax <option> <host>
        if '-h' in sys.argv:
            idx_option = sys.argv.index('-h')
        elif '--host' in sys.argv:
            idx_option = sys.argv.index('--host')
        else:
            raise ValueError('only -h and --host accepted as options\n \
                                <option> <host>')
        # set host
        host = sys.argv[idx_option+1]
        asyncio.run(main(host))
    else:
        asyncio.run(main())
 