# Rhizome bot engine

### Introduction

Rhizome is a conversational bot engine created by Botanic/SEED team that uses .Bot specification to define a conversational bot and runs .Flow intermediate language to determine the flow of the conversation.

Part of the SEED token project. This is a sneak preview - there is more to come.
See [the Wiki](https://github.com/SeedVault/SEEDtoken-IP/wiki) for more information.

## Features
- Support .Bot v1.1 (see https://github.com/SeedVault/bot)
- Support .Flow v1.0
- Support .Flow v2.0 with basic functionality (see https://github.com/SeedVault/flow)
- Template engine support for text output compatible with Templetor.

## To-do

- Add support for .Flow v2.0 full specification.
- Add .Flow instructions to support AIML and ChatScript compiler.
- Add extensions to support all .Flow v2.0 instructions, functions, filters and operators.
- Add channels Skype, Slack, Facebook, Signal, Kik and Twitter.
- Add commands for bot developer and channels to control bot flow and session.

## Getting Started

These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes.

### Prerequisites

* Python 3.7+ and pipenv
* Docker

### Build

```
pipenv shell
./build.sh
cd docker && docker exec -it docker_mongo_1 bash /seed/seedmongo.sh rhizomedb && cd ..
```

Note: If you have issues with `pipenv install` try this:
```
pip install --upgrade pip
pip install git+https://github.com/pypa/pipenv.git
```

Note: If you have issues with `pip install` try this:
```
python3 -m pip install pipenv
```

## Running console channel

```
BBOT_ENV=development python -m channels.console.app <userId> <botIdOrName> <orgId> debug|nodebug
```

**userId**: Any alphanumeric ID to identify yourself.\
**botIdOrName**: The bot ID or bot name you want to run. You can find this in dotbot collection in mongo database\
**orgId**: Organization ID (not supported yet).\
**debug|nodebug**: debug will show the raw json object returned by the bot engine. nodebug will just show text.

Try the included demo bot with:
```
BBOT_ENV=development python -m channels.console.app joe testbot 1 debug
```

## Running a RESTful web server and a simple chatbot web widget (plain text only)

```
BBOT_ENV=development gunicorn "channels.restful.app:create_app()" -b localhost:5000 --reload
```

Open a web browser and navigate to http://localhost:5000/TestWebChatBot

## Running Telegram channel

Run this first to set Telegram web-hooks of all bots with Telegram channel enabled in its .Bot configuration.
```
BBOT_ENV=development python -m channels.telegram.webhooks_check
``` 
 
This runs the Telegram web-hook server on port 5001. 
Be sure to configure a reverse-proxy server to listen to the Telegram web-hooks properly.

```
BBOT_ENV=development gunicorn "channels.telegram.app:create_app()" -b localhost:5001 --reload
```

## Running Dot Repository server
This is a RESTful server used to access .Bot and .Flow databases by Greenhouse and Dandelion.

```
BBOT_ENV=development gunicorn "dot_repository.api:app" -b localhost:8000 --reload
```


## Disclaimer

These files are made available to you on an as-is and restricted basis, and may only be redistributed or sold to any third party as expressly indicated in the Terms of Use for Seed Vault.

### About the SEED Token Project
SEED democratizes AI by offering an open and independent alternative to the monopolies of a few large corporations that currently control conversational user interfaces (CUIs) and AI technologies. SEED's licensed, monetized open-source platform for bots on blockchain supports collaboration and creative compensation that will exceed the proprietary deployments from industry giants. We are also giving users back control of their personal data. Find out more about the SEED Token project at [seedtoken.io](https://seedtoken.io). See the Connect section at the end for contact info.

### Documentation
- [.Flow standard](https://github.com/SeedVault/flow) to know more about the standard used to create the conversation dialogs.
- [.Bot description](https://github.com/SeedVault/bot) to see the format of the configuration file used by Rhizome to create bots.

### Connect
Feel free to throw general questions regarding SEED and what to expect in the following months here on GitHub (or GitLab) at  @consiliera (gaby@seedtoken.io) :sunny: 

**Connect with us elsewhere** 
- [Follow us on Twitter](https://twitter.com/SEED_token)
- Always here the latest news first on [Telegram](https://t.me/seedtoken) and [Discord](https://discord.gg/Suv5bFT)

Seed Vault Code (c) Botanic Technologies, Inc. Used under license.
