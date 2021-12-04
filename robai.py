import os
import openai
import sys
import shelve
import datetime
import argparse

import rich

NOW = datetime.datetime.today()
openai.api_key = os.getenv("OPENAI_API_KEY")

PRE_PROMPT = """Robert is a chatbot that politely answers questions.
###
User: How many pounds are in a kilogram?
Robert: Good question! There are 2.2 pounds in a kilogram.
###"""

# Create the parser
my_parser = \
argparse.ArgumentParser(
                        prog=sys.argv[0],
                        allow_abbrev=True,
                        add_help=True,
                        usage="$(prog)s [-h] prompt",
                        description='Use GPT-3 to complete a response',
                        epilog='(C) Rob')

# Add the arguments
my_parser.add_argument('Prompt',
                       metavar='path',
                       nargs=1,
                       action="store",
                       type=str,
                       help='the prompt GPT-3 should reply to')

my_parser.add_argument('-l',
                       '--long',
                       action='store_true',
                       help='enable long',)

# Execute the parse_args() method
args = my_parser.parse_args()

NEW_PROMPT = f"""
User: {args.Prompt[0]}"""
ROB = """
Robert:"""

with shelve.open('ai_convos.db') as db:
    for date in reversed(sorted(db.keys())):
        if (NOW-datetime.datetime.fromisoformat(date)).total_seconds() < 3600 * 4:
            PRE_PROMPT += db[date]
        else:
            break

        if PRE_PROMPT.length > 1000:
            break

    response = openai.Completion.create(
      engine="davinci-instruct-beta-v3",
      prompt=PRE_PROMPT+NEW_PROMPT+ROB,
      max_tokens=150,
      n=1,
      temperature=0.9
    ).choices[0].text
    rich.print(f"{PRE_PROMPT}{NEW_PROMPT}\n[black on red]Robert: {response}[/black on red]")
    db[str(NOW)] = f"{NEW_PROMPT}\nRobert:{response}\n###"

