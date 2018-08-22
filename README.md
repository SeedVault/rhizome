# BBot bot engine

### Introduction

BBot is a conversational bot engine created by Botanic/SEED team that uses .Bot specification to define a conversational bot and .Flow standard to determine the flow of the conversation.

Part of the SEED token project. This is a sneak preview - there is more to come.
See [the Wiki](https://github.com/SeedVault/SEEDtoken-IP/wiki) for more information.


## Work in progress
The project is still under heavy development. The alpha version will be released during August 2018.

A full working version of the bot engine could be found as proof of concept on [Botanic's repository](https://github.com/botanicinc/bbot-php) built with PHP language.

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
