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
    CREATE USER 'ap'@'%' IDENTIFIED BY '1qaz@WSX';
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