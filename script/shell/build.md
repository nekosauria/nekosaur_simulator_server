# 本次部署以 ubuntu 26.04, Python 3.14.4 為例
# 確認環境版本
```
cat /etc/os-release
python3 --version
```

## scp project
```
mkdir -p /opt/nekosaur

scp nekosaur_simulator_server to /opt/nekosaur ...

sudo chown -R teddy:teddy /opt/nekosaur
```

# add python venv & venv install package
```
cd /opt/nekosaur/nekosaur_simulator_server
python3 -m venv .venv
source .venv/bin/activate
which python3
which pip
pip install --upgrade pip
pip install -r requirements.txt
```

# add systemd service
## 增加 flask app systemd
sudo vi /etc/systemd/system/nekosaur_simulator_server.service

```
[Unit]
Description=Nekosaur Simulator Flask Server
After=network.target mariadb.service rabbitmq-server.service

[Service]
Type=simple
User=teddy
WorkingDirectory=/opt/nekosaur/nekosaur_simulator_server
Environment=PYTHONPATH=/opt/nekosaur/nekosaur_simulator_server/app
ExecStart=/opt/nekosaur/nekosaur_simulator_server/.venv/bin/python app.py
Restart=on-failure
RestartSec=5
StandardOutput=append:/opt/nekosaur/nekosaur_simulator_server/log/app.log
StandardError=append:/opt/nekosaur/nekosaur_simulator_server/log/app_error.log

[Install]
WantedBy=multi-user.target
```

## 增加 apscheduler systemd, 確保在 flask 啟動後才啟動
sudo vi /opt/nekosaur/wait_for_app.sh
```
#!/bin/bash
# wait_for_app: polls health endpoint, fails loudly on timeout
URL="http://127.0.0.1:5656/"
TIMEOUT=600   # 10 分鐘,依模型載入時間可再調整
INTERVAL=2
elapsed=0

until curl -sf "$URL" >/dev/null; do
    sleep "$INTERVAL"
    elapsed=$((elapsed + INTERVAL))
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
        echo "wait_for_app: timeout after ${TIMEOUT}s waiting for $URL" >&2
        exit 1
    fi
    echo "wait_for_app: still waiting... (${elapsed}s elapsed)"
done

echo "wait_for_app: app is up after ${elapsed}s"
```
chmod +x /opt/nekosaur/wait_for_app.sh



sudo vi /etc/systemd/system/nekosaur_aps_scheduler.service
```
[Unit]
Description=Nekosaur APScheduler Producer
After=network.target nekosaur_simulator_server.service
Requires=nekosaur_simulator_server.service
BindsTo=nekosaur_simulator_server.service

[Service]
Type=simple
User=teddy
WorkingDirectory=/opt/nekosaur/nekosaur_simulator_server
Environment=PYTHONPATH=/opt/nekosaur/nekosaur_simulator_server/app
ExecStartPre=/opt/nekosaur/wait_for_app.sh
ExecStart=/opt/nekosaur/nekosaur_simulator_server/.venv/bin/python aps_scheduler.py
Restart=on-failure
RestartSec=5
StandardOutput=append:/opt/nekosaur/nekosaur_simulator_server/log/scheduler.log
StandardError=append:/opt/nekosaur/nekosaur_simulator_server/log/scheduler_error.log

[Install]
WantedBy=multi-user.target
# enable systemd
```

# 啟動/關閉/檢查 service
sudo systemctl daemon-reload

sudo systemctl enable nekosaur_simulator_server.service
sudo systemctl enable nekosaur_aps_scheduler.service

sudo systemctl start nekosaur_simulator_server.service
sudo systemctl start nekosaur_aps_scheduler.service

sudo systemctl status nekosaur_simulator_server.service
sudo systemctl status nekosaur_aps_scheduler.service

sudo systemctl stop nekosaur_aps_scheduler.service
sudo systemctl stop nekosaur_simulator_server.service

sudo journalctl -u nekosaur_simulator_server.service -f
sudo journalctl -u nekosaur_aps_scheduler.service -f