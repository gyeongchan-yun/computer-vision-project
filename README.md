# 2019 Fall Computer Vision Term Project

20195159 Gyeongchan Yun

## Prerequisites: Virtualenv Setting

  - Ubuntu / macOS
    ```
    $ virtualenv venv --python=python3.5
    $ source ./venv/bin/activate
    $ pip install -r requirements.txt
    ```

## Execution

  - FC-DenseNet103 (baseline)
    ```
    $ ./run.sh org
    ```
  - FC-DenseNet103-RBB
    ```
    $ ./run.sh rbb
    ```
  - FC-DenseNet103-RB
    ```
    $ ./run.sh rb
    ``` 

## Original Code
  - https://github.com/AI-slam/FC-DenseNet-Tiramisu
