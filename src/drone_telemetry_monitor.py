import asyncio
import os
from mavsdk import System
import threading
from datetime import datetime
import csv
from utils import haversine_distance

class DroneTelemetryMonitor:
    def __init__(self, drone):
        self.csv_parent_path = "/mnt/c/Users/lucas/Workspace/unexpected_scenario_handling_system/res/collected_data/"
        self.current_csv_name = self.get_current_csv_name("PX4_collected_telemetry_{}.csv")
        self.drone = drone
        self.scenario_name = ""
        self.telemetry_data = {
            "time": None,
            "action":None,
            "target_distance":None,
            "origin_distance": None,
            "velocity.north": None,
            "velocity.east": None,
            "velocity.down": None,
            "battery": None,
            "current_lat":None,
            "current_lon":None,
            "current_alt":None,
            "origin_lat":None,
            "origin_lon":None,
            "origin_alt":None,
            "target_lat":None,
            "target_lon":None,
            "target_alt":None,
            "onWater":None,
            "bad_connection":None,
            "is_armed" : False,
            "goals":""
        }

        self.tasks = []
    
    def get_current_csv_name(self, template_csv_name):
        files = os.listdir(self.csv_parent_path)
        num_files = len(files)

        return template_csv_name.format(num_files)
    
    async def save_telemetry_data(self):

        # Verificar se o arquivo já existe ou precisa ser criado
        current_file_path = os.path.join(self.csv_parent_path, self.current_csv_name)
        while(True):
            file_exists = False
            try:
                with open(current_file_path, 'r'):
                    file_exists = True
            except FileNotFoundError:
                file_exists = False

            # Abrir o arquivo CSV para escrita (adicionando novas linhas)
            with open(current_file_path, mode='a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.telemetry_data.keys())

                # Se o arquivo não existia, escrever o cabeçalho
                if not file_exists:
                    writer.writeheader()

                # Escrever a linha de dados
                writer.writerow(self.telemetry_data)

            await asyncio.sleep(1)




    def get_telimetry(self):
        return self.telemetry_data
    
    def set_scenario(self, scenario_name):
        self.scenario_name = scenario_name
    
    def set_origin_position(self,lat,lon,alt):
        self.telemetry_data["origin_lat"] = lat
        self.telemetry_data["origin_lon"] = lon
        self.telemetry_data["origin_alt"] = alt

    def set_target_position(self,lat,lon,alt):
           self.telemetry_data["target_lat"] = lat
           self.telemetry_data["target_lon"] = lon
           self.telemetry_data["target_alt"] = alt

    async def monitor_scenario_name(self):
        while True:
            self.telemetry_data["time"] = datetime.now().strftime("%H:%M:%S")
            await asyncio.sleep(1)
    
    async def monitor_bad_connection(self):
     async for health in self.drone.telemetry.health():
        if not health.is_global_position_ok:
            self.telemetry_data["bad_connection"] = True
        else:
            self.telemetry_data["bad_connection"] = False
        await asyncio.sleep(1)

    async def monitor_time(self):
        while True:
            self.telemetry_data["scenario_name"] = self.scenario_name
            await asyncio.sleep(1)

    async def monitor_velocity(self):
        async for velocity in self.drone.telemetry.velocity_ned():
            self.telemetry_data["velocity.north"] = velocity.north_m_s
            self.telemetry_data["velocity.east"] = velocity.east_m_s
            self.telemetry_data["velocity.down"] = velocity.down_m_s
            # print(f"Velocidade: Norte {velocity.north_m_s} m/s, Leste {velocity.east_m_s} m/s, Descendo {velocity.down_m_s} m/s")
            await asyncio.sleep(1)

    async def monitor_battery(self):
        async for battery in self.drone.telemetry.battery():
            self.telemetry_data["battery"] = battery.remaining_percent
            # print(f"Bateria: {battery.remaining_percent}%")
            # await asyncio.sleep(1)
    
    async def monitor_target_distance(self):
        while True:
            if self.telemetry_data["current_lat"] == None:
                await asyncio.sleep(1)
                continue

            self.telemetry_data["target_distance"] = haversine_distance(self.telemetry_data["current_lat"],
                                                                             self.telemetry_data["current_lon"],
                                                                             self.telemetry_data["target_lat"],
                                                                             self.telemetry_data["target_lon"])
            await asyncio.sleep(1)

    async def monitor_origin_distance(self):
        while True:
            if self.telemetry_data["current_lat"] == None:
                await asyncio.sleep(1)
                continue

            self.telemetry_data["origin_distance"] = haversine_distance(self.telemetry_data["current_lat"],
                                                                            self.telemetry_data["current_lon"],
                                                                            self.telemetry_data["origin_lat"],
                                                                            self.telemetry_data["origin_lon"])
            await asyncio.sleep(1)
        
    async def monitor_current_position_and_altitude(self):
        async for position in self.drone.telemetry.position():
            if position.latitude_deg is not None:
                self.telemetry_data["current_lat"] = position.latitude_deg
                self.telemetry_data["current_lon"] = position.longitude_deg
                self.telemetry_data["current_alt"] = round(position.relative_altitude_m, 1)

    
    async def monitor_is_armed(self):
        async for arm_status in self.drone.telemetry.armed():
            self.telemetry_data["is_armed"] = arm_status
            await asyncio.sleep(1)
             

    async def _start_monitoring(self):
        tasks = [
            self.monitor_time(),
            self.monitor_scenario_name(),
            self.monitor_current_position_and_altitude(),
            self.monitor_target_distance(),
            self.monitor_origin_distance(),
            self.monitor_bad_connection(),
            self.monitor_velocity(),
            self.monitor_battery(),
            self.save_telemetry_data(),
            self.monitor_is_armed()
        ]
        await asyncio.gather(*tasks)

    def stop_monitoring(self):
        # Cancela todas as tarefas armazenadas
        for task in self.tasks:
            task.cancel()
        print("Todas as tarefas de monitoramento foram canceladas.")
            
    def start_monitoring(self):
        loop = asyncio.get_event_loop()
        loop.create_task(self._start_monitoring())