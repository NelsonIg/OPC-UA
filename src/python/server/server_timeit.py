import asyncio
from asyncua import ua, Server, uamethod
from asyncua.common.subscription import SubHandler
from asyncua import Node, ua

import logging, sys

logging.basicConfig(level=logging.DEBUG) # logging.INFO as default
_logger = logging.getLogger(__name__)

#*********************** Server Methods *******************************#
# add start, stop methods for motor
# @uamethod: Method decorator to automatically
# convert arguments and output to and from variant
@uamethod
async def start_motor(parent):
    pass


@uamethod
async def stop_motor(parent):
    pass


async def main(host='0.0.0.0'):
    # init server, set endpoint
    server = Server()
    await server.init()
    server.set_endpoint(f"opc.tcp://{host}:4840")

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

    # start
    async with server:
        while True:
            await asyncio.sleep(1)

if __name__ == '__main__':

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