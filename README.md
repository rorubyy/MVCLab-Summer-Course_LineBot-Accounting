# Linebot accounting

* **How to run**
    * **Step 1: Install InfluxDB**
        ```
        sudo curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
        sudo echo "deb https://repos.influxdata.com/ubuntu bionic stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
        sudo apt update
        sudo apt install influxdb
        pip install influxdb
        ```
    * **Step 2: Start InfluxDB service****
      ```
      sudo systemctl enable influxdb
      sudo systemctl start influxdb
      sudo service influxdb start
      ```
    * **Step 3: Run ngrok**
        * > ngrok http 8787
    * **Step 4: Test LineBot**
        * > python main.py

## Indtroduction
Accounting
- command
  - `#note [事件] [+/-] [錢]`   -> 新增記帳資料 ex. #note lunch - 100
  - `#report`                  -> 顯示目前記帳資料 
  - `#delete [事件]`           -> 刪除特定事件資料 ex. #delete 1 (delete item of index 1) 
  - `#sum [time shift]`        -> 結算[time shift]天的帳 ex. #sum 2 (show the sum of the recent two days)

