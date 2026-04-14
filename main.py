import asyncio
from dotenv import load_dotenv
import logging
from mavsdk import System
from mavsdk.telemetry import Telemetry
from mavsdk.mission import (MissionItem, MissionPlan)
from dataclasses import dataclass


@dataclass
class Configs():
    mission_kmz_path: str
    telemetry_delay: int | None
    log_telemetry: bool

    @staticmethod
    def __validate_path(path: str | None) -> str:
        if not path:
            raise Exception("aaa")
        return str(path)

    # AdHoc env loading logic
    def __init__(self) -> None:
        from os import getenv
        validate = Configs.__validate_path

        mission_kmz_path = getenv("MISSION_KMZ_PATH")
        logging_file = getenv("LOGGING_FILE_PATH")
        telemetry_logging_delay = getenv("TELEMETRY_LOGGING_DELAY")
        log_telemetry = getenv("LOG_TELEMETRY")

        self.log_telemetry = bool(log_telemetry) if log_telemetry else True

        self.mission_kmz_path = validate(mission_kmz_path) if mission_kmz_path else validate("plans/default.kmz")
        if telemetry_logging_delay:
            self.telemetry_delay = int(telemetry_logging_delay)

        logging_args = {
            'format': '[%(asctime)s] %(message)s',
            'datefmt': '%m/%d/%Y %I:%M:%S %p',
            'encoding': 'utf-8'
        }

        if logging_file:
            logging_args['filename'] = validate(logging_file)
            logging_args['filemode'] = 'w'

        logging.basicConfig(**logging_args)


class DroneController():

    class __TelemetryController():
        def __init__(self):
            self.telemetry = None
            self.configs = None

        async def start(self, telemetry: Telemetry, configs: Configs):
            self.telemetry = telemetry
            self.configs = configs

        async def close(self):
            if self.configs is None or not self.configs.log_telemetry:
                return

    def __init__(self, configs: Configs):
        self.__drone = System()
        self.__telemetry = self.__TelemetryController()
        self.__configs = configs

    async def connect(self):
        await self.__drone.connect()

        async for state in self.__drone.core.connection_state():
            if state.is_connected:
                logging.info("Connected!")
                break

        async for health in self.__drone.telemetry.health():
            if health.is_global_position_ok and health.is_home_position_ok:
                logging.info("Global position estimate!")
                break

        await self.__telemetry.start(self.__drone.telemetry, self.__configs)

    async def close(self):
        await self.__telemetry.close()

    async def run_mission(self):
        pass


async def main():

    drone = DroneController(Configs())

    await drone.connect()

    await drone.run_mission()

if __name__ == '__main__':
    load_dotenv()

    logging.warning("aiaiai")
    asyncio.run(main())
