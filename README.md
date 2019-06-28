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