# BBot bot engine

### Introduction

BBot is a conversational bot engine created by Botanic/SEED team that uses .Bot specification to define a conversational bot and .Flow standard to determine the flow of the conversation.

Part of the SEED token project. This is a sneak preview - there is more to come.
See [the Wiki](https://github.com/SeedVault/SEEDtoken-IP/wiki) for more information.

## Features
- Runs .Flow v1.0 with flow extensions support for Text, Buttons, Media cards, Forms, Send email, Variable storing and comparisson operators.
- Template engine support for text output compatible with Jinja2. Added weather report function.
- Intent match plugins support for regular expressions, ChatScript patterns and Microsoft's Cognitive Service Luis.

## To-do

- Support .Flow v2.0 full specification.
- Support .Bot v1.1.
- Add extensions to support all .Flow v2.0 functions, filters and operators.
- Add channels Telegram, Skype, Slack, Facebook, Signal, Kik and Twitter.
- Add debug response with executed functions and its responses, matched paths and current node data.
- Add commands for bot developer and channels to control bot flow and session.

## Getting Started

These instructions will get you a copy of the project up and running on your
local machine for development and testing purposes.

### Prerequisites

* Python 3.7 or newer
* [Pipenv](http://www.dropwizard.io/1.0.2/docs/)
* [Graphviz](https://www.graphviz.org) (optional)
* [MongoDB](https://www.mongodb.com/) & [ChatScript](https://github.com/bwilcox-1234/ChatScript) server ...
* ... or [docker-compose](https://docs.docker.com/compose/)


### Installation steps

1) Clone project repository:

```
git clone git@github.com:botanicinc/bbot-py.git
```

2) Use pipenv to create a virtual environment:

```
cd bbot-py
pipenv shell
```

3) Install all the dependencies, including the development packages:

```
pipenv install --dev
```

4) (Optional) Install service dependencies (MongoDB & ChatScript Server):

```
cd docker
docker-compose pull
docker-compose build
docker-compose up -d
cd ..
```

5) Create folder **instance** and copy configuration files:

```
mkdir instance
cp ./instance_examples/.env_development_example ./instance/.env_development
cp ./instance_examples/.env_testing_example ./instance/.env_testing
cp ./instance_examples/config_development_example.yml ./instance/config_development.yml
cp ./instance_examples/config_testing_example.yml ./instance/config_testing.yml
```

6) Copy sample bot and its script:

```
cp ./instance_examples/flow_dotbot_example.json ./instance/flow_dotbot.json
cp ./instance_examples/flow_script_example.json ./instance/flow_script.json
```

7) Edit files **./instance/.env_development** and **./instance/.env_testing**
to change configuration settings.


## Running tests

```
make test
```

## Running console channel

```
make console
```

## Running web channel

```
make web
```

Open a web browser and navigate to http://localhost:5000/TestWebChatBot

## Disclaimer

These files are made available to you on an as-is and restricted basis, and may only be redistributed or sold to any third party as expressly indicated in the Terms of Use for Seed Vault.

### About the SEED Token Project
SEED democratizes AI by offering an open and independent alternative to the monopolies of a few large corporations that currently control conversational user interfaces (CUIs) and AI technologies. SEED's licensed, monetized open-source platform for bots on blockchain supports collaboration and creative compensation that will exceed the proprietary deployments from industry giants. We are also giving users back control of their personal data. Find out more about the SEED Token project at [seedtoken.io](https://seedtoken.io). See the Connect section at the end for contact info.

### Documentation
- [.Flow standard](https://github.com/SeedVault/flow) to know more about the standard used to create the conversation dialogs.
- [.Bot description](https://github.com/SeedVault/bot) to see the format of the configuration file used by BBOT to create bots.

### Connect
Feel free to throw general questions regarding SEED and what to expect in the following months here on GitHub (or GitLab) at  @consiliera (gaby@seedtoken.io) :sunny: 

**Connect with us elsewhere** 
- [Follow us on Twitter](https://twitter.com/SEED_token)
- Always here the latest news first on [Telegram](https://t.me/seedtoken) and [Discord](https://discord.gg/Suv5bFT)

Seed Vault Code (c) Botanic Technologies, Inc. Used under license.
