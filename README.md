# Caddy Fileserver

---

## Setup

### Install dependencies

```shell
pip install -r requirements.txt
```

### Create a `systemd` file

```shell
sudo su
nano /etc/systemd/system/fileserver.service
```

```shell
[Unit]
Description=Caddy fileserver
Requires=network.target

[Service]
Type=idle
User=root
WorkingDirectory=<FILESERVER_DATA_PATH>
ExecStart=/usr/bin/caddy file-server --root <FILESERVER_DATA_PATH> --listen :<FILESERVER_PORT>
Restart=always

[Install]
WantedBy=multi-user.target
```

### Enable and start the service

```shell
systemctl daemon-reload
systemctl enable fileserver.service # start on boot
systemctl start fileserver.service
```

---

## Basic Usage

```python
python main.py <file>
```
