#! /bin/bash
mongoimport --db $1 --collection dotbot --file /seed/dotbot.json
mongoimport --db $1 --collection dotflow --file /seed/dotflow.json
mongoimport --db $1 --collection organizations --file /seed/organizations.json
mongoimport --db $1 --collection users --file /seed/users.json
