# GarageBot

#### This telegram bot is used to switch a relay, which controls a remote control of a garage.

## Functions:

- Allows easy switching or opening for a period of time
- Can close the garage after arriving or leaving
- Determines the presence by pinging the owner's smartphone in WiFi
- Warns before closing and allows a break-off
- Allows usage via Telegram only for specific users
- Notifies the owner about the use of the bot by other registered users


## Project Setup

I have soldered two wires to the switch of the garage remote to bridged it. Then the wires were connected to a relay. This relay is controlled by a Raspberry Pi.

<img src="images/setting.jpg" width="350"/>


## Installation
For installation on a Raspberry Pi:
```
git clone https://github.com/Andre0512/GarageBot && cd GarageBot
python3 -m venv venv && source ./venv/bin/activate # optional
pip install -r requirements.txt
```

#### Enter required data into `config.py`
```
cp config.py.default config.py && nano config.py
```
For this step, you have to register a Telegram bot by the Telegram [@BotFahter](https://t.me/botfather).

You can see the Telegram IDs by using an alternative Telegram Client like [Plus Messenger](https://play.google.com/store/apps/details?id=org.telegram.plus) for Android or using the [@userinfobot](https://telegram.me/userinfobot)

#### Start
```
python garage.py &
```

#### Autostart
Execute this command to start the GarageBot automatically at startup:
```
(cat /etc/crontab && echo "@reboot root $PWD/venv/bin/python $PWD/garage.py") | sudo tee /etc/crontab
```


## Screenshot of the Bot
The finished bot looks like this:

<img src="images/screenshot.jpg" width="260"/>
