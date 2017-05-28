# GarageBot

#### This telegram bot is used to switch a relay, which controls a remote control of a garage.

## Functions:

- Allows easy switching and opening for a period of time
- Can close the garage after arriving or leaving
- Determines the presence by pinging the owner's smartphone
- Warns before closing and allows a break-off
- Allows access via Telegram only for registered users
- Notify the owner about the access of other registered users

## Installation
For the Installation on a Raspberry Pi:
```
git clone https://github.com/Andre0512/GarageBot
pip3 install python-telegram-bot
pip3 install pyyaml
```
#### Rename the strings file in your language to `strings.yml`
```
cp strings.yml.english strings.yml
```
#### Enter required data into `config.yml`
```
cp config.yml.default config.yml
```
For this Step, you have to register a Telegram Bot by the Telegram [BotFahter](https://t.me/botfather).

You can see the Telegram ids by using a alternative Telegram Client like 'Plus Messanger' for Android or using `https://api.telegram.org/bot<yourtoken>/getUpdates`
#### Start
```
python3 garage.py &
```

## Project Setup

We have solder 2 wires to the switch of the garage remote control. I connected the wires with a relay. This relay is be controlled by a Raspberry Pi.

<img src="https://github.com/Andre0512/GarageBot/blob/master/images/setting.jpg" width="350"/>

## Screenshot of the Bot
<img src="https://github.com/Andre0512/GarageBot/blob/master/images/screenshot.jpg" width="240"/>
