
----


# export package (optional)

## 更新 requirements.txt 語法
'''
cd ～/<your_py_path>/bin
./python3 -m pip freeze > requirements.txt
'''

## install package by requirements.txt
'''
pip install -r requirements.txt
'''


----


# intel A770 gpu pytorch package (optional)
# 以 ubuntu 為例 (26.04 已經有原生支持)

# 參考文件
https://docs.pytorch.org/docs/2.13/notes/get_start_xpu.html


----

# 安裝 intel torch 套件
## 選擇對應 .venv
cd /opt/nekosaur/nekosaur_simulator_server
source .venv/bin/activate
which python3
which pip



## install require package (先刪除舊的版本)
pip uninstall -y torch torchvision torchaudio cuda-toolkit nvidia-cudnn-cu13 nvidia-nccl-cu13
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/xpu


## 檢查 python torch 腳本, 必須回傳是 Ture Ture 才行
python3 -c "import torch; print(f'API Supported : {hasattr(torch, \"xpu\")}\nIs Available  : {torch.xpu.is_available() if hasattr(torch, \"xpu\") else False}'); print(f'Device Count  : {torch.xpu.device_count()}\nDevice Name   : {torch.xpu.get_device_name(0)}') if hasattr(torch, 'xpu') and torch.xpu.is_available() else None"
