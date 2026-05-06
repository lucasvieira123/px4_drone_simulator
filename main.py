import asyncio
from typing import Any, Callable
from dotenv import load_dotenv
import logging
from mavsdk import System
from mavsdk.telemetry import Telemetry
from mavsdk.mission import (MissionItem, MissionPlan)
from dataclasses import dataclass
from functools import wraps
from threading import Thread, Event
from copy import deepcopy

DEFAULT_PLAN_PATH = "./plans/default.plan"


@dataclass
class Configs():
    mission_plan_path: str
    telemetry_delay: int | None
    log_telemetry: bool

    @staticmethod
    def __validate_path(path: str | None) -> str:
        if not path:
            raise Exception("aaa")
        return str(path)

    @staticmethod
    def __ends_with(val: str, end: str) -> str:
        if not val.endswith(end):
            raise Exception("aaa")
        return val

    def validate_mission_plan(self):
        Configs.__ends_with(Configs.__validate_path(self.mission_plan_path),
                            ".plan")

    # AdHoc env loading logic
    def __init__(self) -> None:
        from os import getenv
        validate = Configs.__validate_path
        ends_with = Configs.__ends_with

    

        mission_plan_path = getenv("MISSION_PLAN_PATH")
        logging_file = getenv("LOGGING_FILE_PATH")
        telemetry_logging_delay = getenv("TELEMETRY_LOGGING_DELAY")
        log_telemetry = getenv("LOG_TELEMETRY")

        self.log_telemetry = bool(log_telemetry) if log_telemetry else True

        self.mission_plan_path = ends_with(
            validate(mission_plan_path if mission_plan_path else DEFAULT_PLAN_PATH), 
            ".plan"
        )

        if telemetry_logging_delay:
            self.telemetry_delay = int(telemetry_logging_delay)
        else:
            self.telemetry_delay = None

        logging_args = {
            'format': '[%(asctime)s] %(message)s',
            'datefmt': '%m/%d/%Y %I:%M:%S %p',
            'encoding': 'utf-8'
        }

        if logging_file:
            logging_args['filename'] = validate(logging_file)
            logging_args['filemode'] = 'w'

        logging.basicConfig(**logging_args)


@dataclass
class RelativeMissionItem:
    lat: float
    long: float
    alt: float


class RelativeMissionPlan:
    def __init__(self, init_point: MissionItem):
        self.__points = [init_point]

    def add(self, item: MissionItem | RelativeMissionItem):
        if isinstance(item, MissionItem):
            self.__points.append(item)
        else:
            self.__points.append(deepcopy(self.__points[-1]))
            self.__points[-1].latitude_deg += item.lat
            self.__points[-1].longitude_deg += item.long
            self.__points[-1].relative_altitude_m += item.alt

    def to_MissionPlan(self) -> MissionPlan:
        return MissionPlan(self.__points)


class DroneController():
    class __TelemetryController():

        def __init__(self, telemetry: Telemetry, configs: Configs):
            self.telemetry = telemetry
            self.configs = configs
            self.tasks: list[asyncio.Task] = []
            self.stop_event = Event()

        async def close(self):
            self.stop_event.set()

            asyncio.gather(*self.tasks)

        async def position(self, ctx: dict[str, Any], shutdown: bool = False):
            pos = "pos"
            if shutdown:
                if pos in ctx:
                    ctx[pos].aclose()
                return

            positions = self.telemetry.position()

            if pos not in ctx:
                ctx[pos] = positions

            async for p in positions:
                logging.warning(f"position: {p}")
                break

        async def logging_cicle(self, func: Callable[[dict[str, Any], bool]],
                                stop_event: Event):
            ctx = dict()
            while not stop_event.is_set():
                await func(ctx, False)
                if self.configs.telemetry_delay is not None:
                    await asyncio.sleep(self.configs.telemetry_delay)
            await func(ctx, True)

        async def run(self):
            funcs = [self.position]

            for func in funcs:
                self.tasks.append(
                        asyncio.create_task(self.logging_cicle(func,
                                                               self.stop_event)
                                            )
                    )

    def __init__(self, configs: Configs):
        self.__drone = System()
        self.__telemetry: DroneController.__TelemetryController | None = None
        self.__configs = configs
        self.__mission_loaded = False

    @staticmethod
    def __loads_mission_dec(fun: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fun)
        def wrapper(self, *args, **kwargs):
            out = fun(self, *args, **kwargs)
            self.__mission_loaded = True
            return out

        return wrapper

    async def run_mission(self, falty=False) -> bool:
        """
            Runs the already loaded mission

            falty: if true raise errors
        """
        if not self.__mission_loaded:
            if falty:
                raise Exception("Trying to run without a mission loaded")
            return False
        await self.__drone.action.arm()
        logging.warning("-- Armed")

        await self.__drone.action.takeoff()
        logging.warning("-- take off")

        await self.__drone.mission.start_mission()
        logging.warning("-- mission started")

        if self.__telemetry is not None:
            await self.__telemetry.run()

        return True

    async def connect(self):
        """
            Manages the connection to PX4 drone
        """
        await self.__drone.connect()

        async for state in self.__drone.core.connection_state():
            if state.is_connected:
                logging.info("Connected!")
                break

        async for health in self.__drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                logging.info("Global position estimate!")
                break

        self.__telemetry = self.__TelemetryController(self.__drone.telemetry,
                                                      self.__configs)

    async def close(self):
        """
            Garantees that the connections are closed
        """
        if self.__telemetry is not None:
            await self.__telemetry.close()

    @__loads_mission_dec
    async def import_mission(self, path=""):
        """
            Imports and loads a .plan file passed as argument.

            if no plan_path is provided or it is equal to the empty sting
            tries to import from the environment variables
        """
        if path == "":
            self.__configs.validate_mission_plan()
            path = self.__configs.mission_plan_path
        out = await self.__drone.mission_raw.import_qgroundcontrol_mission(path)
        # TODO: Consider if storing this is needed

        await self.__drone.mission_raw.upload_mission(out.mission_items)
        await self.__drone.mission_raw.upload_rally_points(out.rally_items)
        # await self.__drone.mission_raw.upload_geofence(out.geofence_items)

    @__loads_mission_dec
    async def upload_mission_by_items(self, items: list[MissionItem]):
        """
            Uploads a mission to the drone using mavsdk.mission.MissionItem
        """
        return await self.set_mission(MissionPlan(items))

    @__loads_mission_dec
    async def set_mission(self, mission_plan: MissionPlan):
        """
            Uploads a mission to the drone using mavsdk.mission.MissionPlan
        """
        await self.__drone.mission.upload_mission(mission_plan)


async def main():

    drone = DroneController(Configs())

    await drone.connect()
    await drone.import_mission()
    if await drone.run_mission():
        pass
    else:
        logging.warning("-- misison failed")

    await asyncio.sleep(1000)

if __name__ == '__main__':
    load_dotenv()

    asyncio.run(main())
