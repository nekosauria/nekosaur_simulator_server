# 參考網站
# https://www.rabbitmq.com/docs/install-debian#apt-quick-start
# e.g. ubuntu 24.04 apt repo

# 下載 package
```
#!/bin/sh

sudo apt-get install curl gnupg apt-transport-https -y

## Team RabbitMQ's signing key
curl -1sLf "https://keys.openpgp.org/vks/v1/by-fingerprint/0A9AF2115F4687BD29803A206B73A36E6026DFCA" | sudo gpg --dearmor | sudo tee /usr/share/keyrings/com.rabbitmq.team.gpg > /dev/null

## Add apt repositories maintained by Team RabbitMQ
sudo tee /etc/apt/sources.list.d/rabbitmq.list <<EOF
## Modern Erlang/OTP releases
##
deb [arch=amd64 signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://deb1.rabbitmq.com/rabbitmq-erlang/ubuntu/noble noble main
deb [arch=amd64 signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://deb2.rabbitmq.com/rabbitmq-erlang/ubuntu/noble noble main

## Latest RabbitMQ releases
##
deb [arch=amd64 signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://deb1.rabbitmq.com/rabbitmq-server/ubuntu/noble noble main
deb [arch=amd64 signed-by=/usr/share/keyrings/com.rabbitmq.team.gpg] https://deb2.rabbitmq.com/rabbitmq-server/ubuntu/noble noble main
EOF

## Update package indices
sudo apt-get update -y

## Install Erlang packages
sudo apt-get install -y erlang-base \
                        erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets \
                        erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key \
                        erlang-runtime-tools erlang-snmp erlang-ssl \
                        erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl

## Install rabbitmq-server and its dependencies
sudo apt-get install rabbitmq-server -y --fix-missing

```


# 使用 repo 預設版本
```
vi /etc/apt/preferences.d/erlang
    Package: erlang*
    Pin: release o=RabbitMQ
    Pin-Priority: 1001
    
sudo apt-cache policy | grep rabbit
apt-cache policy erlang-base
```

# start rabbitmq
```
systemctl start rabbitmq-server
systemctl enable rabbitmq-server
systemctl status rabbitmq-server
```

# add web management ui 
```
# 啟用外掛（開啟 15672 埠）
sudo rabbitmq-plugins enable rabbitmq_management

# 新增管理者帳號（預設 guest 帳號只能從 localhost 登入）
sudo rabbitmqctl add_user admin "your_password"

# 設置最高權限標籤 (administrator)
sudo rabbitmqctl set_user_tags admin administrator

# 賦予虛擬主機 (Virtual Host) 的讀寫存取權限
sudo rabbitmqctl set_permissions -p "/" admin ".*" ".*" ".*"

netstat -tplnu
```

# 建立 vhost
```
#!/usr/bin/env bash
set -e

# 建立 Virtual Hosts (VHosts)
echo "==> 建立 VHosts..."
sudo rabbitmqctl add_vhost /nekosaur

# 建立統一的服務帳號 ap
echo "==> 建立使用者 ap..."
sudo rabbitmqctl add_user ap "your_password"

# 將兩個 VHost 的權限都賦予 ap (配置、寫入、讀取皆為全開 ".*")
echo "==> 設定 ap 存取兩個 VHost 的權限..."
sudo rabbitmqctl set_permissions -p "/nekosaur" ap ".*" ".*" ".*"

# (選用) 若有 admin 帳號，也一併授權方便 UI 監控
sudo rabbitmqctl set_permissions -p "/nekosaur" admin ".*" ".*" ".*" || true

# (選用) 刪除不需要的 guest user
sudo rabbitmqctl delete_user guest

echo "==> 設定完成！"
```

# 檢查 vhost
```
# 1. 查看系統中的所有 VHosts
sudo rabbitmqctl list_vhosts

# 2. 查看特定 VHost 的權限配置
sudo rabbitmqctl list_permissions -p /nekosaur
```