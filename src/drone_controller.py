from utils.logger import Logger
from mavsdk import System
from drone_telemetry_monitor import DroneTelemetryMonitor
import asyncio


class DroneController:
    def __init__(self, drone : System, logger : Logger):
        self.drone = drone
        self.logger = logger
        self.monitor = DroneTelemetryMonitor(drone, logger)

    async def execute_mission(self):
        goal = False

        

        self.monitor.set_target_position(-3.786700, -38.551971, 10)
   
        self.logger.info("Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok and health.is_armable:
                self.logger.info("-- Global position estimate OK")
                break
            await asyncio.sleep(1)

        async for position in self.drone.telemetry.position():
            if position.latitude_deg is not None:
                self.monitor.set_origin_position(position.latitude_deg,
                                             position.longitude_deg,
                                             position.relative_altitude_m)
                break

            await asyncio.sleep(0.5)
        

        self.monitor.start_monitoring()
        
        await asyncio.sleep(5)

        self.logger.info("-- Arming")
        self.monitor.set_action("Arm")
        await self.drone.action.arm()
        
        while(True):
            if self.monitor.get_telimetry()["current_lat"] is None:
                await asyncio.sleep(0.5)
            else:
                break

        self.logger.info("-- Taking off")
        self.monitor.set_action("TakeOff")
        await self.drone.action.goto_location(self.monitor.get_telimetry()["current_lat"],
                                        self.monitor.get_telimetry()["current_lon"], 10, 0)
        # await drone.action.takeoff()
        altura = self.monitor.get_telimetry()["current_alt"]
        while(altura<9.5):
            await asyncio.sleep(1)
            altura = self.monitor.get_telimetry()["current_alt"]
            self.logger.info(f"Altura: {altura}")

        self.logger.info("-- Flying")
        self.monitor.set_action("Flying")
        

        await self.drone.action.goto_location(self.monitor.get_telimetry()["target_lat"],
                                              self.monitor.get_telimetry()["target_lon"],
                                              self.monitor.get_telimetry()["target_alt"], 0)
        target_distance = 999999
        while target_distance>=0.5:
            await asyncio.sleep(1)
            target_distance=self.monitor.get_telimetry()["target_distance"]
            
            self.logger.info(f"Target Distance: {target_distance}")

        await asyncio.sleep(5)

        self.logger.info("-- Landing")
        self.monitor.set_action("Landing")
        await self.drone.action.land()

        altura = self.monitor.get_telimetry()["current_alt"]
        while(altura>0.0):
            await asyncio.sleep(1)
            altura = self.monitor.get_telimetry()["current_alt"]
            self.logger.info(altura)

        await asyncio.sleep(2)    
        
        self.monitor.set_action("Disarm")
        await self.drone.action.disarm()

        await asyncio.sleep(3)
        self.monitor.stop_monitoring()

        # async for is_armed in self.drone.telemetry.armed():
        #     while(True):
        #         if is_armed:
        #             print(f"is_armed: {is_armed}")
        #             await asyncio.sleep(1)
        #         else:
        #             print(f"is_armed: {is_armed}")
        #             self.monitor.stop_monitoring()
        #             break
                    

        goal = True

        # await asyncio.sleep(10)

        

        return goal
