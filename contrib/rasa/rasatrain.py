#!/usr/bin/python3

from rasa_nlu.training_data import load_data
from rasa_nlu.model import Trainer
from rasa_nlu import config
import sys
import os

import os
bindir = os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) != 3:
  sys.stderr.write("Usage: rasatrain.py <rasa-json-training-file> <output-directory>\n")
  exit(1)

jsonfile = sys.argv[1]
outdir = sys.argv[2]

training_data = load_data(jsonfile)
trainer = Trainer(config.load(bindir + "/config_spacy.yml"))
trainer.train(training_data)
model_directory = trainer.persist('.', None, '.', outdir)
print(model_directory)
