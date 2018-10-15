#!/usr/bin/python3

import sys

import os
bindir = os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) != 2:
  sys.stderr.write("Usage: rasaparse.py <rasa-json-training-file> < input.txt\n")
  exit(1)

model_directory = sys.argv[1]
from rasa_nlu.model import Interpreter

# where model_directory points to the model folder
interpreter = Interpreter.load(model_directory)

for line in sys.stdin:
  line = line.rstrip()
  out = interpreter.parse(line)
  print(out["intent"]["name"] + "\t" + line)
  sys.stderr.write(str(out) + "\n")
