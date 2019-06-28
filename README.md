# augustpy

Because the August Connect is far too expensive.

## Setup

These instructions are currently for Linux *only*. The Raspberry Pi 3 and newer are supported, as well as the Zero W.

### Automated setup

Simply run `setup.sh` to install requirements and configure permissions. Root access is required.

### Manual setup

1. Setup basic packages:
```bash
  $ sudo apt-get install python3 python3-pip libglib2.0-dev
```

2. Clone repo to desired location and enter the folder.

2. Install Python requirements:
```bash
  $ pip3 install -r requirements.txt
```

3. **[Recommended]** To use Bluetooth LE scanning functionality as non-root, give direct permissions to `bluepy-helper`:
```bash
  $ sudo setcap 'cap_net_raw,cap_net_admin+eip' $(echo "$(pip3 show bluepy | grep Location: | cut -c 11-)/bluepy/bluepy-helper")
```

## Configuration

Communication with the lock is encrypted using a hidden key stored within the August app. In order to control and monitor your August lock with this program, you must first find this key.

### Android Phone

**Root is required to access the data.** If your phone is not rooted, you may be able to setup a rooted Android virtual machine, install the August app on it and extract the necessary data from there.

If the phone is rooted, you can copy the settings file `/data/data/com.august.luna/shared_prefs/PeripheralInfoCache.xml` from your phone to your computer. Apps such as Solid Explorer can do this, or you may use `adb shell`.

Open `PeripheralInfoCache.xml` and find the `bluetoothAddress`, `handshakeKey` and `handshakeKeyIndex` strings. You should find something like this:
```xml
&quot;bluetoothAddress&quot;:&quot;0A:1B:2C:3D:4E:5F&quot;,&quot;handshakeKey&quot;:&quot;ABCDEF0123456789ABCDEF0123456789&quot;,&quot;handshakeKeyIndex&quot;:1
```

Copy the values found between the `&quot;` delimiters (here, `0A:1B:2C:3D:4E:5F`, `ABCDEF0123456789ABCDEF0123456789` and `1`, respectively).

### iPhone

The key and offset can be found in plist located at:

    User Applications/August/Library/Preferences/com.august.iossapp.plist

This can be retrieved by using a file explorer like [http://www.i-funbox.com/ifunboxmac/](iFunBox), and opening the plist in Xcode.

### Putting it all together

Paste the values you've found in a file named `config.json` in the folder you wish to execute augustpy from, like so:
```json
{"bluetoothAddress": "0A:1B:2C:3D:4E:5F", "handshakeKey": "ABCDEF0123456789ABCDEF0123456789", "handshakeKeyIndex": 1}
```

If you have more than one lock, you may instead define an array of locks, like so:
```json
[
  {"name": "front", "bluetoothAddress": "0A:1B:2C:3D:4E:5F", "handshakeKey": "ABCDEF0123456789ABCDEF0123456789", "handshakeKeyIndex": 1},
  {"name": "back", "bluetoothAddress": "6A:7B:8C:9D:0E:1F", "handshakeKey": "ABCDEF0123456789ABCDEF0123456789", "handshakeKeyIndex": 1}
]
```