#!/usr/bin/env python3
"""
Server which
    - controls DC Motor
    - computes RPM


Object: DC Motor
    Variables: inp_value, rounds_per_min
    Methods: start_motor(), stop_motor()
"""
import sys
sys.path.insert(0, '..') # import parent folder

import asyncio # documentation --> https://docs.python.org/3/library/asyncio-task.html
from asyncua import ua, Server, uamethod
from asyncua.common.subscription import SubHandler
from asyncua import Node, ua

from gpiozero import Motor, Button

import logging

from multiprocessing import Process, Value

import time
import numpy as np

puls = Button(14)

logging.basicConfig(level=logging.INFO) # logging.INFO as default
_logger = logging.getLogger() #'asyncua')

#*********************** Callback functions *******************************#
global MOTOR_STARTED, NEW_MOTOR_INP
global STOP_FLAG, START_FLAG

class SubscriptionHandler (SubHandler):
    """
    Handle the data that received for the subscription.
    """

    def datachange_notification(self, node: Node, val, data):
        global STOP_FLAG, START_FLAG, NEW_MOTOR_INP, motor_speed_is
        print(f'datachange_notification node: {node} value: {val}')
        motor_speed_is = val
        if val > 0:
            START_FLAG=True
        else:
            STOP_FLAG=True
        NEW_MOTOR_INP=True

# Define Flags as multiprocessing.Value so memory is shared
global EDGE_DETECTED, OLD_EDGE, NEW_EDGE
EDGE_DETECTED = Value('i', False)
OLD_EDGE, NEW_EDGE = Value('i', False), Value('i', False)

def callback_high_edge():
    global EDGE_DETECTED, OLD_EDGE, NEW_EDGE
    OLD_EDGE.value = NEW_EDGE.value
    NEW_EDGE.value = time.perf_counter_ns()
    EDGE_DETECTED.value = True




#*********************** Server Methods *******************************#
START_FLAG, STOP_FLAG, NEW_MOTOR_INP = False, False, False # inititate flags
# add start, stop methods for motor
# @uamethod: Method decorator to automatically
# convert arguments and output to and from variant
@uamethod
async def start_motor(parent):
    global  START_FLAG
    if not START_FLAG:
        START_FLAG = True
        print("Motor started.")


@uamethod
async def stop_motor(parent):
    global STOP_FLAG
    if not STOP_FLAG:
        STOP_FLAG = True
        print("Motor stopped")

#*********************** Other functions *******************************#
global dc_motor_inp, dc_motor_rpm, motor_speed_is

global motor
motor = Motor(26, 20)
async def set_speed():
    global START_FLAG, STOP_FLAG, NEW_MOTOR_INP, motor_speed_is
    if START_FLAG:
        if NEW_MOTOR_INP:
            motor.forward(motor_speed_is)
            NEW_MOTOR_INP = False
            START_FLAG = False
            print(f'motor set to {motor_speed_is}')
    if STOP_FLAG:
        motor.forward(0)
        NEW_MOTOR_INP = True
        STOP_FLAG = False
        print(f'motor set to 0')

global mean_diff
mean_diff = Value('i', 0)
def clalc_time_diff():
    """
        Calculate Time Difference between pulses
    """
    print('Thread started')
    counter = 0
    n_pulses = 5
    diff = 0
    diff_vec = np.zeros(n_pulses) # stores last time differences of pulses
    while True:
        global EDGE_DETECTED, OLD_EDGE,\
                NEW_EDGE, mean_diff

        if EDGE_DETECTED.value:
            EDGE_DETECTED.value = False
            counter = 0

            if NEW_EDGE.value and OLD_EDGE.value:
                # update mean difference between pulses
                diff = NEW_EDGE.value-OLD_EDGE.value
                if diff >0: # ignore random wrong values
                    diff_vec[1::] = diff_vec[:-1:1]
                    diff_vec[0] = diff
        else:
            counter +=1
            if counter>50: diff_vec = np.zeros(n_pulses)
        mean_diff.value = int(np.mean(diff_vec))
        # print(f'Thread\tdiff: {diff}')
        # print(f'Thread\tdiff_vec: {diff_vec}')
        # print(f'Thread\tmean_diff: {mean_diff.value}')
        time.sleep(0.001)

async def set_rpm():
    global mean_diff, dc_motor_rpm
    # print(f'async\tmean_diff {mean_diff.value}')
    if mean_diff.value==0:
        rpm=0
    else:
        rpm = 60/((mean_diff.value)*20*(10**(-9)))
    await dc_motor_rpm.write_value(rpm)
    print('rpm\t',rpm)

async def main(host='localhost'):
    # init server, set endpoint
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://{host}:4840/server_example/")

    # setup of namespace, not needed
    uri = "example-uri.edu"
    idx = await server.register_namespace(uri)

    # Create new object type
    base_obj_motor = await server.nodes.base_object_type.add_object_type(nodeid=idx, bname="BaseMotor")
    base_var_rpm = await base_obj_motor.add_variable(nodeid=idx, bname="RPM", val=0.0)
    base_var_inp = await base_obj_motor.add_variable(nodeid=idx, bname="Input", val=0.0)
    # ensure that variable will be instantiated together with object
    await base_var_rpm.set_modelling_rule(True)
    await base_var_inp.set_modelling_rule(True)

    # Address Space
    dc_motor = await server.nodes.objects.add_object(nodeid=idx, bname="Motor", objecttype=base_obj_motor)
    global dc_motor_inp, dc_motor_rpm
    dc_motor_inp = await dc_motor.get_child(f'{idx}:Input')
    dc_motor_rpm = await dc_motor.get_child(f'{idx}:RPM')
    await dc_motor_inp.set_writable()
    await dc_motor_rpm.set_writable()
    # add methods
    await dc_motor.add_method(idx, "start_motor", start_motor, [], [])
    await dc_motor.add_method(idx, "stop_motor", stop_motor, [], [])
    # subscription
    sub_handler = SubscriptionHandler()
    subscription = await server.create_subscription(period=10, handler=sub_handler)
    # subscribe to data change, only current data queuesize=1
    await subscription.subscribe_data_change(nodes=dc_motor_inp, queuesize=1)

    # start
    async with server:
        while True:
            await asyncio.gather(set_speed(), set_rpm())
            await asyncio.sleep(.50)

if __name__ == "__main__":
    p = Process(target=clalc_time_diff)
    p.start()

    if len(sys.argv)>1:
        host = sys.argv[1]
    else:
        host='localhost'
    try:
        asyncio.run(main(host))
    except Exception as e:
        print(e)
        p.kill()
        p.join()