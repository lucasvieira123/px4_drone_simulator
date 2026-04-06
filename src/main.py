# Exemplo de uso da classe
import asyncio
from drone_controller import DroneController
from simulation_controller import SimulationController
import time
from mavsdk import System
from utils.logger import DefaultLogger, Logger
import subprocess
import os

async def run(logger : Logger):
    num_of_execution = 1
    current_execution = 1

    simulador_controller = SimulationController(logger)

    while current_execution<=num_of_execution:
        simulador_controller.start_all_processes()

        drone = System()
        await drone.connect(system_address="udp://:14540")

        logger.info("Waiting for drone to connect...")
        async for state in drone.core.connection_state():
            if state.is_connected:
                logger.info(f"-- Connected to drone!")
                break

        drone_controller = DroneController(drone, logger)
        goal = await drone_controller.execute_mission()
        simulador_controller.kill_all_process()
        

        await asyncio.sleep(10)
        # simulador_controller.start_all_processes()
        current_execution = current_execution +1

     

if __name__ == "__main__":
    # Inicia os processos

    logger = DefaultLogger()

    try:
        asyncio.run(run(logger))
    except KeyboardInterrupt:
        print("Interrompido pelo usuário.")
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Constrói o caminho completo para o script bash
        script_path = os.path.join(parent_dir, "kill_between_make_and_ruby.sh")
        # Executa o script bash
        subprocess.run([script_path], shell=True, executable='/bin/bash')

    # Reinicia o processo PX4_Autopilot após algum tempo (exemplo)
    # Aqui você pode adicionar um tempo de espera ou uma condição específica para reiniciar
    # manager.reset_PX4_Autopilot_process()

    # Se necessário, você pode terminar todos os processos
    # manager.stop_all_processes()
