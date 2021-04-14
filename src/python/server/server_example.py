#!/usr/bin/env python3
'''
Example of OPC UA Server populated with custom Object DC Motor

Object: DC Motor
    Variables: inp_value, rounds_per_min
    Methods: start_motor(), stop_motor()
'''
import sys
sys.path.insert(0, '..') # import parent folder
import asyncio
from asyncua import ua, Server, uamethod



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
        print("Motor stopped\n")

# simulate motor
async def motor_simulation():
    """
    simulate a dc motor
    """
    global MOTOR_STARTED, dc_motor_inp, dc_motor_rpm
    while True:
        while MOTOR_STARTED:
            inp = await dc_motor_inp.get_value() # motor input
            rpm_fin = inp*10 # final rpm value
            rpm_now = await dc_motor_rpm.get_value() # current rpm value
            if rpm_fin>rpm_now: # increase rpm
                await dc_motor_rpm.write_value(rpm_now+inp/10)
            elif rpm_fin<rpm_now: # decrease rpm
                await dc_motor_rpm.write_value(rpm_now - inp / 10)
            else: # do nothing
                pass
            await asyncio.sleep(0.1) # sleep 100ms
        # motor stopped
        await dc_motor_rpm.write_value(0)
        await asyncio.sleep(0.1)  # sleep 100ms


async def main():
    # init server, set endpoint
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://localhost:4840/server_example/")

    # setup of namespace, not needed
    uri = "example-uri.edu"
    idx = await server.register_namespace(uri)

    # Create new object type dc_motor_base
    base_obj_motor = await server.nodes.base_object_type.add_object_type(nodeid=idx, bname="BaseMotor")
    base_var_rpm = await base_obj_motor.add_variable(nodeid=idx, bname="RPM", val=0.0)
    base_var_inp = await base_obj_motor.add_variable(nodeid=idx, bname="Input", val=0.0)
    # ensure that variable will be instanciated together with object
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
    await dc_motor.add_method(idx,  # nodeid
                              "start_motor",  # browsename
                              start_motor,  # method to be called
                              [],  # list of input arguments
                              [],  # list output arguments
                              )
    await dc_motor.add_method(idx, "stop_motor", stop_motor, [], [])

    # create task for simulation of dc motor
    task_motor_sim = asyncio.create_task(motor_simulation())
    # start
    async with server:
        while True:
            await task_motor_sim # runs concurrently with main()
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
