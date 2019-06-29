import bluepy.btle as btle
from Cryptodome.Cipher import AES
from . import util
import time


class SessionDelegate(btle.DefaultDelegate):
    def __init__(self, session):
        btle.DefaultDelegate.__init__(self)
        self.session = session
        self.data = None

    def handleNotification(self, cHandle, data):
        if self.data is not None:
            return

        data = self.session.decrypt(data)
        self.session._validate_response(data)
        self.data = data


class Session:
    cipher_encrypt = None
    cipher_decrypt = None

    def __init__(self, peripheral):
        self.peripheral = peripheral

    def set_write(self, write_characteristic):
        self.write_characteristic = write_characteristic

    def set_read(self, read_characteristic):
        self.read_characteristic = read_characteristic

    def set_key(self, key: bytes):
        self.cipher_encrypt = AES.new(key, AES.MODE_CBC, iv=bytes(0x10))
        self.cipher_decrypt = AES.new(key, AES.MODE_CBC, iv=bytes(0x10))

    def decrypt(self, data: bytearray):
        if self.cipher_decrypt is not None:
            cipherText = data[0x00:0x10]
            plainText = self.cipher_decrypt.decrypt(cipherText)
            if type(data) is not bytearray:
                data = bytearray(data)
            util._copy(data, plainText)

        return data

    def build_command(self, opcode: int):
        cmd = bytearray(0x12)
        cmd[0x00] = 0xee
        cmd[0x01] = opcode
        cmd[0x10] = 0x02
        return cmd

    def _write_checksum(self, command: bytearray):
        checksum = util._simple_checksum(command)
        command[0x03] = checksum

    def _validate_response(self, response: bytearray):
        if util._simple_checksum(response) != 0:
            raise Exception("Simple checksum mismatch")

        if response[0x00] != 0xbb and response[0x00] != 0xaa:
            raise Exception("Incorrect flag in response")

    def _write(self, command: bytearray):
        print("Writing command: " + command.hex())

        # NOTE: The last two bytes are not encrypted
        # General idea seems to be that if the last byte
        # of the command indicates an offline key offset (is non-zero),
        # the command is "secure" and encrypted with the offline key
        if self.cipher_encrypt is not None:
            plainText = command[0x00:0x10]
            cipherText = self.cipher_encrypt.encrypt(plainText)
            util._copy(command, cipherText)

        print("Encrypted command: " + command.hex())

        delegate = SessionDelegate(self)

        self.peripheral.withDelegate(delegate)
        self.write_characteristic.write(command, True)
        if delegate.data is None and \
                self.peripheral.waitForNotifications(10) is False:
            raise Exception("Notification timed out")

        return delegate.data

    def execute(self, command: bytearray):
        self._write_checksum(command)
        return self._write(command)


class SecureSession(Session):

    def __init__(self, peripheral, key_index):
        super().__init__(peripheral)
        self.key_index = key_index

    def set_key(self, key: bytes):
        self.cipher_encrypt = AES.new(key, AES.MODE_ECB)
        self.cipher_decrypt = AES.new(key, AES.MODE_ECB)

    def build_command(self, opcode: int):
        cmd = bytearray(0x12)
        cmd[0x00] = opcode
        cmd[0x10] = 0x0f
        cmd[0x11] = self.key_index
        return cmd

    def _write_checksum(self, command: bytearray):
        checksum = util._security_checksum(command)
        checksum_bytes = checksum.to_bytes(4, byteorder='little', signed=False)
        util._copy(command, checksum_bytes, destLocation=0x0c)

    def _validate_response(self, data: bytes):
        if util._security_checksum(data) != int.from_bytes(data[0x0c:0x10], byteorder='little', signed=False):
            raise Exception("Security checksum mismatch")