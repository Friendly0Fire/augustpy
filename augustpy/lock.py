import bluepy.btle as btle
import Cryptodome.Random
from . import session, util

class Lock:
    COMMAND_SERVICE_UUID        = btle.UUID("0000fe24-0000-1000-8000-00805f9b34fb")
    WRITE_CHARACTERISTIC        = btle.UUID("bd4ac611-0b45-11e3-8ffd-0800200c9a66")
    READ_CHARACTERISTIC         = btle.UUID("bd4ac612-0b45-11e3-8ffd-0800200c9a66")
    SECURE_WRITE_CHARACTERISTIC = btle.UUID("bd4ac613-0b45-11e3-8ffd-0800200c9a66")
    SECURE_READ_CHARACTERISTIC  = btle.UUID("bd4ac614-0b45-11e3-8ffd-0800200c9a66")

    def __init__(self, address, keyString, keyIndex):
        self.address = address
        self.key = bytes.fromhex(keyString)
        self.key_index = keyIndex
        self.name = None

        self.peripheral = None
        self.session = None
        self.secure_session = None
        self.command_service = None
        self.is_secure = False

    def set_name(self, name):
        self.name = name

    def connect(self):
        self.peripheral = btle.Peripheral(self.address)
        if self.name is None:
            self.name = self.peripheral.addr

        self.session = session.Session(self.peripheral)
        self.secure_session = session.SecureSession(self.peripheral, self.key_index)

        self.command_service = self.peripheral.getServiceByUUID(self.COMMAND_SERVICE_UUID)

        characteristics = self.command_service.getCharacteristics()
        for characteristic in characteristics:
            if characteristic.uuid == self.WRITE_CHARACTERISTIC:
                self.session.set_write(characteristic)
            elif characteristic.uuid == self.READ_CHARACTERISTIC:
                self.session.set_read(characteristic)
            elif characteristic.uuid == self.SECURE_WRITE_CHARACTERISTIC:
                self.secure_session.set_write(characteristic)
            elif characteristic.uuid == self.SECURE_READ_CHARACTERISTIC:
                self.secure_session.set_read(characteristic)

        self.secure_session.set_key(self.key)

        handshake_keys = Cryptodome.Random.get_random_bytes(16)

        # Send SEC_LOCK_TO_MOBILE_KEY_EXCHANGE
        cmd = self.secure_session.build_command(0x01)
        util._copy(cmd, handshake_keys[0x00:0x08], destLocation=0x04)
        response = self.secure_session.execute(cmd)
        if response[0x00] != 0x02:
            raise Exception("Unexpected response to SEC_LOCK_TO_MOBILE_KEY_EXCHANGE: " +
                            response.hex())

        self.is_secure = True

        session_key = bytearray(16)
        util._copy(session_key, handshake_keys[0x00:0x08])
        util._copy(session_key, response[0x04:0x0c], destLocation=0x08)
        self.session.set_key(session_key)
        self.secure_session.set_key(session_key)

        # Send SEC_INITIALIZATION_COMMAND
        cmd = self.secure_session.build_command(0x03)
        util._copy(cmd, handshake_keys[0x08:0x10], destLocation=0x04)
        response = self.secure_session.execute(cmd)
        if response[0] != 0x04:
            raise Exception("Unexpected response to SEC_INITIALIZATION_COMMAND: " +
                            response.hex())

        return True

    def force_lock(self):
        cmd = self.session.build_command(0x0b)
        return self.session.execute(cmd)

    def force_unlock(self):
        cmd = self.session.build_command(0x0a)
        return self.session.execute(cmd)

    def lock(self):
        if self.status() == 'unlocked':
            return self.force_lock()

        return True

    def unlock(self):
        if self.status() == 'locked':
            return self.force_unlock()

        return True

    def status(self):
        cmd = bytearray(0x12)
        cmd[0x00] = 0xee
        cmd[0x01] = 0x02
        cmd[0x04] = 0x02
        cmd[0x10] = 0x02

        response = self.session.execute(cmd)
        status = response[0x08]

        strstatus = 'unknown'
        if status == 0x02:
            strstatus = 'unlocking'
        elif status == 0x03:
            strstatus = 'unlocked'
        elif status == 0x04:
            strstatus = 'locking'
        elif status == 0x05:
            strstatus = 'locked'

        if strstatus == 'unknown':
            print("Unrecognized status code: " + hex(status))

        return strstatus

    def disconnect(self):

        # if self.is_secure:
        #     cmd = self.secure_session.build_command(0x05)
        #     cmd[0x11] = 0x00
        #     response = self.secure_session.execute(cmd)

        #     if response[0] != 0x8b:
        #         raise Exception("Unexpected response to DISCONNECT: " +
        #                         response.hex())

        self.peripheral.disconnect()

        return True

    def is_connected(self):
        return type(self.session) is session.Session \
            and self.peripheral.addr is not None
