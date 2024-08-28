#!/bin/bash


echo "processes: $(ps -u $USER)"
# Encontre o PID do primeiro processo make
make_pid=$(ps -u $USER | grep '[m]ake' | awk 'NR==1 {print $1}')

# Encontre o PID do último processo ruby
last_ruby_pid=$(ps -u $USER | grep '[r]uby' | awk 'END {print $1}')

# Debug: Verifique os valores de make_pid e last_ruby_pid
echo "make_pid: $make_pid"
echo "last_ruby_pid: $last_ruby_pid"

# Verifique se os PIDs foram encontrados
if [[ -z "$make_pid" || -z "$last_ruby_pid" ]]; then
  echo "Erro: Não foi possível encontrar o processo 'make' ou 'ruby'."
  exit 1
fi

# Liste todos os processos do usuário e filtre os PIDs entre make_pid e last_ruby_pid
ps -u $USER -o pid,cmd --sort=pid | awk -v start=$make_pid -v end=$last_ruby_pid '
  $1 > start && $1 <= end { print $1 }
' | xargs -r kill

echo "Processos entre PID $make_pid (make) e $last_ruby_pid (ruby) foram finalizados."

