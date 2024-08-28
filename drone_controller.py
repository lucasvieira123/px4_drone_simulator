
from drone_telemetry_monitor import DroneTelemetryMonitor
import asyncio


class DroneController:
    def __init__(self, drone):
        self.drone = drone
        self.monitor = DroneTelemetryMonitor(drone)

    async def execute_mission(self):
        goal = False

        self.monitor.set_target_position(-3.786700, -38.551971, 5)
   
        print("Waiting for drone to have a global position estimate...")
        async for health in self.drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok and health.is_armable:
                print("-- Global position estimate OK")
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

        print("-- Arming")
        self.monitor.set_scenario("Arm")
        await self.drone.action.arm()
        
        while(True):
            if self.monitor.get_telimetry()["current_lat"] is None:
                await asyncio.sleep(0.5)
            else:
                break

        print("-- Taking off")
        self.monitor.set_scenario("TakeOff")
        await self.drone.action.goto_location(self.monitor.get_telimetry()["current_lat"],
                                        self.monitor.get_telimetry()["current_lon"], 5, 0)
        # await drone.action.takeoff()
        altura = self.monitor.get_telimetry()["current_alt"]
        while(altura<4.5):
            await asyncio.sleep(1)
            altura = self.monitor.get_telimetry()["current_alt"]
            print(f"Altura: {altura}")

        print("-- Flying")
        self.monitor.set_scenario("Flying")
        

        await self.drone.action.goto_location(self.monitor.get_telimetry()["target_lat"],
                                              self.monitor.get_telimetry()["target_lon"],
                                              self.monitor.get_telimetry()["target_alt"], 0)
        target_distance = 999999
        while target_distance>=1.0:
            await asyncio.sleep(1)
            target_distance=self.monitor.get_telimetry()["target_distance"]
            
            print(f"Target Distance: {target_distance}")

        await asyncio.sleep(5)

        print("-- Landing")
        self.monitor.set_scenario("Landing")
        await self.drone.action.land()

        altura = self.monitor.get_telimetry()["current_alt"]
        while(altura>1.0):
            await asyncio.sleep(1)
            altura = self.monitor.get_telimetry()["current_alt"]
            print(altura)

        goal = True

        await asyncio.sleep(10)

        return goal