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


global rising_edge_detected
rising_edge_detected = False

def callback_high_edge():
    global rising_edge_detected
    rising_edge_detected = True

async def main(host='localhost'):
    puls.when_pressed = callback_high_edge # rising edge

    server_endpoint = f"opc.tcp://{host}:4840/server_example/"
    client = Client(url=server_endpoint)
    async with client:
        idx = await client.get_namespace_index(uri="example-uri.edu")
        # get motor object, here path from root folder
        motor_obj = await client.nodes.root.get_child(["0:Objects", f"{idx}:Motor"])
        # get motor rpm variable
        motor_rpm = await client.nodes.objects.get_child(path=[f"{idx}:Motor", f"{idx}:RPM"])

        global rising_edge_detected
        rising_edge_new = None
        diff_vec = np.zeros(5) # stores 5 last time differences of pulses
        counter = 0
        while True:
            if rising_edge_detected:
                rising_edge_detected = False
                counter = 0
                rising_edge_old = rising_edge_new
                rising_edge_new = time.perf_counter_ns()

                if rising_edge_new and rising_edge_old:
                    # updatte mean difference between pulses
                    diff = rising_edge_new-rising_edge_old
                    diff_vec[1::] = diff_vec[:-1:1]
                    diff_vec[0] = diff
            else:
                counter +=1
                if counter>1000: diff_vec = np.zeros(5)
            mean_diff = diff_vec.mean()
            print(mean_diff)


if __name__ == "__main__":
    if len(sys.argv)>1:
        host = sys.argv[1]
    else:
        host='localhost'
    asyncio.run(main(host))
