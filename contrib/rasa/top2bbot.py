#!/usr/bin/python3

import warnings
import sys
import re
import json

question_list = [ ]
answer_map = { }

for line in sys.stdin:
  line = line.rstrip()
  ar = re.search('^\s*u: (\S+)', line)

  if ar:
    # if it's an answer, associate it with the preceding questions
    answer = ar.group(1)
    if len(question_list) == 0:
      warnings.warn('no questions for answer ' + answer)

    answer_map[answer] = question_list
    question_list = [ ]

  else:
    qr = re.search('^#!\s*([^\t#]+)', line)
    if qr:
      # if it's a question, append it to the list
      question = qr.group(1)
      question_list.append(question)
    else: 
      if re.match('^\s*#', line):
        # don't clear question list if there are comment lines
        1
      else:
        if len(question_list):
          warnings.warn('no answer for questions ' + str(question_list))
        question_list = [ ]

out = [ ]

for answer in answer_map:
  questions = answer_map[answer]
  if len(questions) > 0:
    out.append({answer: questions})

print(json.dumps(out))

