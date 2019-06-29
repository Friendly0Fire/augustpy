#!/bin/python3

import augustpy.lock
import json
import time
import argparse

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
    locks.append(lock)

parser = argparse.ArgumentParser(description="Remotely control August locks.")
parser.add_argument('lock', metavar='L', type=str, nargs='+', help="The lock's name or address")
parser.add_argument('--lock', dest='action', action='store_const',
                   const='lock', help='Lock the lock')
parser.add_argument('--unlock', dest='action', action='store_const',
                   const='unlock', help='Lock the lock')
parser.add_argument('--status', dest='action', action='store_const',
                   const='status', help='Request lock status')
parser.set_defaults(action='status')

args = parser.parse_args()

for lock in locks:
    if lock.name in args.lock:
        lock.connect()
        if args.action == 'lock':
            lock.lock()
            print('locked')
        elif args.action == 'unlock':
            lock.unlock()
            print('unlocked')
        elif args.action == 'status':
            print(lock.status())
        lock.disconnect()