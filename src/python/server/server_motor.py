#!/usr/bin/env python3
"""
Server for DC Motor Control

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

class SubscriptionHandler (SubHandler):
    """
    Handle the data that received for the subscription.
    """

    def datachange_notification(self, node: Node, val, data):
        print(f'datachange_notification node: {node} value: {val}')

# add start, stop methods for motor
global MOTOR_STARTED, dc_motor_inp, dc_motor_rpm
MOTOR_STARTED = False
# @uamethod: Method decorator to automatically
# convert arguments and output to and from variant
@uamethod
async def start_motor(parent):
    global  MOTOR_STARTED
    if not MOTOR_STARTED:
        MOTOR_STARTED = True
        print("Motor started.")


@uamethod
async def stop_motor(parent):
    global MOTOR_STARTED
    if MOTOR_STARTED:
        MOTOR_STARTED = False
        print("Motor stopped")



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
            await asyncio.sleep(1)

if __name__ == "__main__":
    if len(sys.argv)>1:
        host = sys.argv[1]
    else:
        host='localhost'
    asyncio.run(main(host))
