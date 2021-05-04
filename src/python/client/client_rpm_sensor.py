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

import time
import numpy as np

puls = Button(14)

logging.basicConfig(level=logging.INFO) # logging.INFO as default
_logger = logging.getLogger() #'asyncua')


global rising_edge_detected, rising_edge_old, rising_edge_new
rising_edge_detected = False
rising_edge_old, rising_edge_new = None, None

def callback_high_edge():
    global rising_edge_detected, rising_edge_old, rising_edge_new
    rising_edge_old = rising_edge_new
    rising_edge_new = time.perf_counter_ns()
    rising_edge_detected = True


global motor_rpm, mean_diff
mean_diff = 0
async def clalc_time_diff():
    """
        Calculate Time Difference between pulses
    """
    global rising_edge_detected, rising_edge_old, rising_edge_new
    rising_edge_new = None
    n_pulses = 10
    diff_vec = np.zeros(n_pulses) # stores 5 last time differences of pulses
    counter = 0
    if rising_edge_detected:
        rising_edge_detected = False
        counter = 0

        if rising_edge_new and rising_edge_old:
            # updatte mean difference between pulses
            diff = rising_edge_new-rising_edge_old
            diff_vec[1::] = diff_vec[:-1:1]
            diff_vec[0] = diff
    else:
        counter +=1
        if counter>4: diff_vec = np.zeros(n_pulses)
    mean_diff = diff_vec.mean()
    # print(mean_diff)
    await asyncio.sleep(0.01)

async def send_rpm():
    while True:
        if mean_diff==0:
            rpm=0
        else:
            rpm = 60/(mean_diff*20*10**(-9))
        await motor_rpm.write_value(rpm)
        print()
        print(rpm)
        asyncio.sleep(0.01)

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


        # task to write to motor_rpm
        task_send_rpm = asyncio.create_task(send_rpm())
        # task to compute mean time difference between pulses
        task_compute_mean = asyncio.create_task(clalc_time_diff())

        
        await task_compute_mean
        print('send rpm started')
        await task_send_rpm


if __name__ == "__main__":
    if len(sys.argv)>1:
        host = sys.argv[1]
    else:
        host='localhost'
    asyncio.run(main(host))
