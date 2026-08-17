# 安裝 mysql
```
sudo apt update

sudo apt install mariadb-server mariadb-client galera-4

# 官方 初始化安全性加固腳本（Security Hardening Script）。
# 設定都 -y 就好, 記得記住 root password
sudo mariadb-secure-installatio

# start service
sudo systemctl status mariadb
sudo systemctl start mariadb
sudo systemctl enable mariadb
sudo systemctl status mariadb

mariadb --version
# mariadb  Ver 15.1 Distrib 10.11.14-MariaDB, for debian-linux-gnu (x86_64) using  EditLine wrapper
```


# 升級套件版本至 mariadb 12.3 lts
```
# https://mariadb.org/download/?t=repo-config&d=24.04+%22noble%22&v=12.3&r_m=xtom_hk

sudo apt-get install apt-transport-https curl
sudo mkdir -p /etc/apt/keyrings
sudo curl -o /etc/apt/keyrings/mariadb-keyring.asc 'https://mariadb.org/mariadb_release_signing_key.pgp'

vi /etc/apt/sources.list.d/mariadb.sources
    # MariaDB 12.3 repository list - created 2026-08-04 09:41 UTC
    # https://mariadb.org/download/
    X-Repolib-Name: MariaDB
    Types: deb
    # deb.mariadb.org is a dynamic mirror if your preferred mirror goes offline. See https://mariadb.org/mirrorbits/ for details.
    # URIs: https://deb.mariadb.org/12.3/ubuntu
    URIs: https://mirrors.xtom.com.hk/mariadb/repo/12.3/ubuntu
    Suites: noble
    Components: main main/debug
    Signed-By: /etc/apt/keyrings/mariadb-keyring.asc

sudo systemctl stop mariadb
netstat -tplnu 

sudo apt-get update
sudo apt-get install mariadb-server

sudo systemctl restart mariadb
sudo systemctl status mariadb

sudo mariadb-upgrade -u root -p

# 檢查 MariaDB 版本
mariadb --version

```


# add user
```
# connection
mariadb -u root -p 

    SHOW DATABASES;
    SHOW ENGINES;
    SHOW VARIABLES LIKE 'default_storage_engine';
    
    system clear
    
    -- 建立資料庫 (使用 utf8mb4 支援多國語言與 Emoji)
    CREATE DATABASE nekosaur_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    
    -- create user && add privileges
    CREATE USER 'ap'@'%' IDENTIFIED BY 'your_password';
    GRANT ALL PRIVILEGES ON nekosaur_db.* TO 'ap'@'%';
    FLUSH PRIVILEGES;
    
    EXIT;

mariadb -u ap -p nekosaur_db

    SHOW DATABASES;
    USE nekosaur_db;
    SHOW TABLES;
```

# set config allow ip
```
sudo vi /etc/mysql/mariadb.conf.d/50-server.cnf
    [mysqld]
    bind-address = 0.0.0.0

sudo systemctl restart mariadb
```