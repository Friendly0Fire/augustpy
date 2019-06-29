import augustpy.lock
import json

config = None

with open("config.json", "r") as config_file:
    config = json.load(config_file)

if type(config) is dict:
    config = [config]

locks = []

for lock_config in config:
    lock = augustpy.lock.Lock(lock_config["bluetoothAddress"], lock_config["handshakeKey"], lock_config["handshakeKeyIndex"])
    if "name" in lock_config:
        lock.set_name(lock_config["name"])
    lock.connect()
    locks.append(lock)

for lock in locks:
    print("Lock " + lock.name + " is currently " + lock.status())
    lock.unlock()
    lock.disconnect()