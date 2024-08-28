import subprocess
import os
import signal
import time

# Comando que você deseja executar
class SimulationController:
    def __init__(self):
        # Comandos que você deseja executar
        self.PX4_Autopilot_command = "cd ~/PX4-Autopilot && make px4_sitl gz_x500"
        self.MicroXRCEAgent_command = "cd ~/ && MicroXRCEAgent udp4 -p 8888"
        self.QGroundControl_command = "cd ~/ && ./QGroundControl.AppImage"

        # Lista dos nomes dos processos que você quer matar
        self.process_names = ["xterm", "make", "cmake", "ninja", "px4", "ruby"]

        # Inicializa os subprocessos
        self.PX4_Autopilot_process = None
        self.MicroXRCEAgent_process = None
        self.QGroundControl_process = None


    def start_all_processes(self):
        """Inicia os subprocessos em terminais separados"""
        if self.PX4_Autopilot_process == None:
            self.PX4_Autopilot_process = subprocess.Popen(
                ["xterm", "-hold", "-e", self.PX4_Autopilot_command],
                preexec_fn=os.setsid  # Define um novo grupo de processos
            )
        if self.MicroXRCEAgent_process == None:
            self.MicroXRCEAgent_process = subprocess.Popen(["xterm", "-e", self.MicroXRCEAgent_command])

        if self.QGroundControl_process == None:
            self.QGroundControl_process = subprocess.Popen(["xterm", "-e", self.QGroundControl_command])

    def kill_all_process(self):
        try:
            if self.PX4_Autopilot_process:
                # Obtém o diretório onde o arquivo Python atual está localizado
                script_dir = os.path.dirname(os.path.abspath(__file__))
                # Constrói o caminho completo para o script bash
                script_path = os.path.join(script_dir, "kill_between_make_and_ruby.sh")
                # Executa o script bash
                subprocess.run([script_path], shell=True, executable='/bin/bash')

                #mata so o terminal que ainda ficou aberto
                os.killpg(os.getpgid(self.PX4_Autopilot_process.pid), signal.SIGTERM)

                self.PX4_Autopilot_process = None

            # if self.MicroXRCEAgent_process:
            #     os.killpg(os.getpgid(self.MicroXRCEAgent_process.pid), signal.SIGTERM)
            #     self.MicroXRCEAgent_process = None

            # self.MicroXRCEAgent_process = None

            # if self.QGroundControl_process:
            #     os.killpg(os.getpgid(self.QGroundControl_process.pid), signal.SIGTERM)
            #     self.QGroundControl_process = None

            # self.QGroundControl_process = None

        except Exception as e:
            print(e)
        
        #Inicia um novo processo PX4_Autopilot
        # self.PX4_Autopilot_process = subprocess.Popen(["xterm", "-hold", "-e", self.PX4_Autopilot_command])
        # print(f"Novo processo PX4_Autopilot iniciado com PID {self.PX4_Autopilot_process.pid}.")