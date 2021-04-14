#!/usr/bin/env python3
"""
Example OPC UA Client
which Subscribes to DC Motor Object Attributes (RPM, Input)
"""

import sys
sys.path.insert(0, "..")
import asyncio
import logging
from asyncua import Client, Node, ua
from asyncua.common.subscription import SubHandler

logging.basicConfig(level=logging.INFO) # logging.INFO as default
_logger = logging.getLogger('asyncua')

global STOP_FLAG
STOP_FLAG = False


class SubscriptionHandler (SubHandler):
    """
    Handle the data that received for the subscription.
    """

    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        global STOP_FLAG
        _logger.info('datachange_notification node: %r value: %s', node, val)
        if val > 1:
            STOP_FLAG = True



async def main():
    """
    Open communication to Server and then sleep forever
    """
    server_endpoint = "opc.tcp://localhost:4840/server_example/"
    client = Client(url=server_endpoint)
    async with client:
        idx = await client.get_namespace_index(uri="example-uri.edu")
        # get motor object, here path from root folder
        motor_obj = await client.nodes.root.get_child(["0:Objects", f"{idx}:Motor"])
        # get motor input variable, here path starting from Object folder
        motor_inp = await client.nodes.objects.get_child(path=[f"{idx}:Motor", f"{idx}:Input"])
        # get motor rpm variable
        motor_rpm = await client.nodes.objects.get_child(path=[f"{idx}:Motor", f"{idx}:RPM"])

        # subscription
        sub_handler = SubscriptionHandler()
        subscription = await client.create_subscription(period=50, handler=sub_handler)
        # subscribe to data change, only current data queuesize=1
        await subscription.subscribe_data_change(nodes=motor_rpm, queuesize=1)

        global STOP_FLAG # flag to stop motor
        # write to input value of motor
        # then, start motor
        # finally, stop motor if stop flag is set by sub_handler
        # and delete subscription and exit context manager
        await motor_inp.write_value(1)
        _logger.info('wrote 20 to input value')
        await motor_obj.call_method(f'{idx}:start_motor')
        _logger.info('motor started')
        while True:
            await asyncio.sleep(0.005)
            if STOP_FLAG:
                await motor_obj.call_method(f"{idx}:stop_motor")
                _logger.info('motor stopped')
                STOP_FLAG = False
                subscription.delete()
                await asyncio.sleep(1)
                break


if __name__ == "__main__":
    asyncio.run(main())


