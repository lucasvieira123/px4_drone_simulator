#!/usr/bin/env python3

import asyncio
from mavsdk import System


async def run():
    # Init the drone
    drone = System()
    await drone.connect()

    # Start the tasks
    # asyncio.ensure_future(print_battery(drone))
    # asyncio.ensure_future(print_gps_info(drone))
    # asyncio.ensure_future(print_in_air(drone))
    


    # asyncio.ensure_future(print_health(drone))
    asyncio.ensure_future(print_position(drone))


    while True:
        # await print_position(drone)
        await asyncio.sleep(1)

async def print_battery(drone):
    async for battery in drone.telemetry.battery():
        print(f"Battery: {battery.remaining_percent}")
        # await asyncio.sleep(1)

async def print_health(drone):
    async for health in drone.telemetry.health():
        print(health)
        # await asyncio.sleep(1)


async def print_gps_info(drone):
    async for gps_info in drone.telemetry.gps_info():
        print(f"GPS info: {gps_info}")
        # await asyncio.sleep(1)


async def print_in_air(drone):
    async for in_air in drone.telemetry.in_air():
        print(f"In air: {in_air}")
        # await asyncio.sleep(1)


async def print_position(drone):
    async for position in drone.telemetry.position():
        print(position)
        # await asyncio.sleep(3)
        


if __name__ == "__main__":
    # Start the main function
    asyncio.run(run())