#!/usr/bin/python3

import json
import sys

import os
bindir = os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) != 2:
  sys.stderr.write("Usage: rasatest.py <rasa-json-training-file> < input.tsv\n")
  exit(1)

model_directory = sys.argv[1]
print(model_directory)
from rasa_nlu.model import Interpreter

# where model_directory points to the model folder
interpreter = Interpreter.load(model_directory)

n_correct = 0
n_samples = 0

for line in sys.stdin:
  line = line.rstrip()
  (target, txt) = line.split("\t")
  out = interpreter.parse(txt)
  intent = out['intent']['name']

  correct = 0
  if intent == target:
    correct = 1
  n_correct += correct
  n_samples += 1

  print("\t".join([intent, target, txt]))

ratio = 0
if n_samples > 0:
  ratio = n_correct/n_samples
sys.stderr.write("correct rate = " + str(ratio) + " (" + str(n_correct) + "/" + str(n_samples) + ")\n")
