#!/usr/bin/env python3

import asyncio
from mavsdk import System
from src.utils import haversine_distance
import math

async def update_position(drone):
    global current_lat, current_lon, current_alt
    async for position in drone.telemetry.position():
        current_lat = position.latitude_deg
        current_lon = position.longitude_deg
        current_alt = position.absolute_altitude_m
        await asyncio.sleep(1)
        break

async def run():

    drone = System()
    await drone.connect(system_address="udp://:14540")

    asyncio.ensure_future(print_status_text(drone))

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"-- Connected to drone!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok and health.is_home_position_ok:
            print("-- Global position estimate OK")
            break

    print("-- Arming")
    await drone.action.arm()

    # asyncio.ensure_future(await update_position(drone))

    await update_position(drone)

    print("-- Taking off")
    await drone.action.goto_location(current_lat, current_lon, 10, 0)
    # await drone.action.takeoff()

    while(current_alt<9.0):
        await asyncio.sleep(1)
        await update_position(drone)
        print(f"Altura:{current_alt}")


    flying_lat = 47.3988109
    flying_lon = 8.5465527
    flying_alt = 0

    await drone.action.goto_location(flying_lat, flying_lon, flying_alt, 0)
    distancia = 999999
    while distancia>=3:
        await asyncio.sleep(1)
        await update_position(drone)
        print(f"Distancia:{distancia}")
        distancia = haversine_distance(current_lat,current_lon, flying_lat, flying_lon)
        

    # await asyncio.sleep(12)

    print("-- Landing")
    await drone.action.land()

    while True:
        print("Staying connected, press Ctrl-C to exit")
        await asyncio.sleep(1)


async def print_status_text(drone):
    try:
        async for status_text in drone.telemetry.status_text():
            print(f"Status: {status_text.type}: {status_text.text}")
    except asyncio.CancelledError:
        return


if __name__ == "__main__":
    # Run the asyncio loop
    asyncio.run(run())