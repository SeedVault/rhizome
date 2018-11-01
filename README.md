# Rhizome bot engine

### Introduction

Rhizome is a conversational bot engine created by Botanic/SEED team that uses .Bot specification to define a conversational bot and runs .Flow intermediate language to determine the flow of the conversation.

Part of the SEED token project. This is a sneak preview - there is more to come.
See [the Wiki](https://github.com/SeedVault/SEEDtoken-IP/wiki) for more information.

## Features
- Support .Bot v1.1 (see https://github.com/SeedVault/bot)
- Support .Flow v1.0 with flow extensions support for Text, Buttons, Media cards, Forms, Send email, Variable storing and comparisson operators.
- Support .Flow v2.0 with basic functionality (see https://github.com/SeedVault/flow)
- Template engine support for text output compatible with Jinja2.

## To-do

- Support .Flow v2.0 full specification.
- Add extensions to support all .Flow v2.0 functions, filters and operators.
- Add channels Skype, Slack, Facebook, Signal, Kik and Twitter.
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
git clone https://github.com/SeedVault/rhizome.git
```

2) Use pipenv to create a virtual environment:

```
cd rhizome
pipenv shell
```

3) Install all the dependencies, including the development packages:

```
pipenv install --dev
pipenv install web.py==0.40.dev1
```

Note: you will get an error message "No matching distribution found for web-py==0.40.dev1". You can ignore this.\
This is an expected result when having installed pip version older than 19.0 (which is not released at the time of writing this)\
For more information see https://github.com/pypa/pip/pull/5875\
\
**Note for developers: If you need to add more packages remember to delete the entry for web-py in Pipfile before committing the code.**

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

6) Edit files **./instance/.env_development** and **./instance/.env_testing**
to change configuration settings.


7) Seed database in the container

This will seed the database with a demo bot.
If you are not using the container you can find the extended json files in /docker/seed folder.

```
docker exec -it docker_mongo_1 bash /seed/seedmongo.sh <databasename>
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
