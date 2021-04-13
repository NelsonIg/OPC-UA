#!/usr/bin/env python3

'''
Example of OPC UA Server populated with custom Object DC Motor

Object: DC Motor
    Variables: inp_value, rounds_per_min
    Methods: start_motor(), stop_motor()
'''

import asyncio
from asyncua import ua, Server, uamethod



# add start, stop methods for motor

# @uamethod: Method decorator to automatically
# convert arguments and output to and from variant
@uamethod
async def start_motor(parent, inp: float):
    print(f"Motor started with input value: {inp}\n")


@uamethod
async def stop_motor(parent):
    print("Motor stopped\n")


async def main():
    # init server, set endpoint
    server = Server()
    await server.init()
    server.set_endpoint("opc.tcp://0.0.0.0:4840/server")

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
    # methods
    start_inp_arg = ua.Argument() # argument for start method
    start_inp_arg.Name = "Motor Input"
    start_inp_arg.DataType = ua.NodeId(ua.ObjectIds.Float)# define as float
    start_inp_arg.ValueRank = -1 # value ranke = -1: value must be scalar
    start_inp_arg.Description = ua.LocalizedText("Relative Input of motor, not dc voltage")
    # add methods
    await dc_motor.add_method(idx,  # nodeid
                              "start_motor",  # browsename
                              start_motor,  # method to be called
                              [start_inp_arg],  # list of input arguments
                              [],  # list output arguments
                              )
    await dc_motor.add_method(idx, "stop_motor", stop_motor, [], [])

    # start
    async with server:
        while True:
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
