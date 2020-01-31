#!/bin/bash

if [ ! $# -eq 1 ]; then
  echo "[USAGE] run.sh [model config]"
  echo "-- org"
  echo "-- rbb"
  echo "-- rb"
  exit 1
fi

config=$1

if [ "$config" == "org" ]; then
  cp ./FC_DenseNet_Tiramisu_org.py ./FC_DenseNet_Tiramisu.py
elif [ "$config" == "rbb" ]; then
  cp ./FC_DenseNet_Tiramisu_RBB.py ./FC_DenseNet_Tiramisu.py
elif [ "$config" == "rb" ]; then
  cp ./FC_DenseNet_Tiramisu_RB.py ./FC_DenseNet_Tiramisu.py
else
  echo "No such model configuration: $config"
  exit 1
fi

source ./venv/bin/activate
python main.py
