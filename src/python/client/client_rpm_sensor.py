#!usr/bin/env python3
'''
    Client to update the rounds per minute of motor
'''
import sys
sys.path.insert(0, "..")
import asyncio
import logging
from asyncua import Client, Node, ua
from gpiozero import Button
from multiprocessing import Process, Value

import time
import numpy as np

puls = Button(14)

logging.basicConfig(level=logging.INFO) # logging.INFO as default
_logger = logging.getLogger() #'asyncua')

# Define Flags as multiprocessing.Value so memory is shared
global rising_edge_detected, rising_edge_old, rising_edge_new
rising_edge_detected = Value('i', 0)
rising_edge_old, rising_edge_new = Value('i', 0), Value('i', 0)

def callback_high_edge():
    global rising_edge_detected, rising_edge_old, rising_edge_new
    rising_edge_old.value = rising_edge_new.value
    rising_edge_new.value = time.perf_counter_ns()
    rising_edge_detected.value = 1


global motor_rpm, mean_diff
mean_diff = Value('d', 0.0)
def clalc_time_diff():
    """
        Calculate Time Difference between pulses
    """
    print('Thread started')
    counter = 0
    while True:
        global rising_edge_detected, rising_edge_old,\
                rising_edge_new, mean_diff

        # rising_edge_new = None
        n_pulses = 10
        diff_vec = np.zeros(n_pulses) # stores last time differences of pulses
        # counter = 0
        if rising_edge_detected.value:
            rising_edge_detected = 0
            counter = 0

            if rising_edge_new.value and rising_edge_old.value:
                # update mean difference between pulses
                diff = rising_edge_new.value-rising_edge_old.value
                diff_vec[1::] = diff_vec[:-1:1]
                diff_vec[0] = diff
        else:
            counter +=1
            if counter>4: diff_vec = np.zeros(n_pulses)
        mean_diff.value = diff_vec.mean()
        print('mean:\t',mean_diff.value)
        time.sleep(0.01)

async def send_rpm():
        if mean_diff.value==0:
            rpm=0
        else:
            rpm = 60/(mean_diff.value*20*10**(-9))
        await motor_rpm.write_value(rpm)
        print('rpm\t',rpm)

async def main(host='localhost'):
    global motor_rpm

    puls.when_pressed = callback_high_edge # rising edge

    server_endpoint = f"opc.tcp://{host}:4840/server_example/"
    client = Client(url=server_endpoint)
    async with client:
        idx = await client.get_namespace_index(uri="example-uri.edu")
        # get motor object, here path from root folder
        motor_obj = await client.nodes.root.get_child(["0:Objects", f"{idx}:Motor"])
        # get motor rpm variable
        motor_rpm = await client.nodes.objects.get_child(path=[f"{idx}:Motor", f"{idx}:RPM"])


        # # task to write to motor_rpm
        # task_send_rpm = asyncio.create_task(send_rpm())
        # task to compute mean time difference between pulses
        

        print('send rpm started')
        while True:
            await task_send_rpm
            asyncio.sleep(0.01)


if __name__ == "__main__":
    p = Process(target=clalc_time_diff)
    p.start()
    if len(sys.argv)>1:
        host = sys.argv[1]
    else:
        host='localhost'
    asyncio.run(main(host))
