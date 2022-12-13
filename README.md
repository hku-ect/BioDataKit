# Bio Data Kit

* main.py: A basic python script to send enviro sensor data through OSC
* BioDataKitActor.py: A Gazebosc Actor to send enviro sensor data
* BioDataKit.gzs: An example Gazebosc stage

![enviro image](https://cdn.shopify.com/s/files/1/0174/1800/products/Enviro-Plus-pHAT-on-white-2_192x192.jpg?v=1573820030)

# Quick Install

Follow the instructions from Pi Moroni to prep your RPI.

From the repo:

```bash
pip install -r requirements.txt
python3 main.py
```

# RPI OS Installation Notes

Make sure to install Raspberry Pi OS (Not Raspbian). As of writing 2022-09-22-raspios-bullseye-armhf.
When booting follow the onscreen setup:

 * Keyboard Layout: Select the right keyboard (`US with EURO on 5`)
 * Create the default user

When the PI has booted login and issue the following command:

```bash
sudo raspi-config
```

In this program set the following options

* System options – hostname: set a sane hostname!
* Interface options – SSH: enable ssh
* Localisation options – Locale: 
  * select en_IE.UTF-8 UTF-8, deselect any other
  * Set en_IE.UTF-8 UTF-8 as default
* Localisation options – Timezone: Select Europe - Amsterdam

# Software Installation Notes

Before installing the software make sure to physically install the enviro board with the power off.

First prepare the RPI for the hardware by issuing the following commands:

```bash
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0
```

# Install extra software dependencies

```bash
sudo apt install python3-numpy python3-smbus python3-pil python3-setuptools python3-pip git
```

Finally install the enviro python libraries:

```bash
sudo python3 -m pip install enviroplus
```

We will be using git to acquire the software. Create a directory where you want the sources to reside, ie ~/src/ and change to the dir

```bash
mkdir ~/src
cd ~/src
```

We will now clone the software repository

```bash
git clone https://github.com/hku-ect/BioDataKit.gitcd BioDataKit
```

If all went well we can now test the sensor board using python3:

```bash
pip3 install -r requirements.txt
python3 main.py
```
