#!/bin/bash

onred='\033[41m'
ongreen='\033[42m'
onyellow='\033[43m'
endcolor="\033[0m"

echo -e "${onyellow}Building Rhizome...$endcolor"

pipenv install --dev
pipenv install web.py==0.40.dev1

# Handle errors
set -e
error_report() {
    echo -e "${onred}Error: failed on line $1.$endcolor"
}
trap 'error_report $LINENO' ERR
cd docker
docker-compose pull
docker-compose build
cd ..
mkdir instance
cp ./instance_examples/.env_development_example ./instance/.env_development
cp ./instance_examples/.env_testing_example ./instance/.env_testing
cp ./instance_examples/config_development_example.yml ./instance/config_development.yml
cp ./instance_examples/config_testing_example.yml ./instance/config_testing.yml

echo -e "${ongreen}Rhizome has been built.$endcolor"
