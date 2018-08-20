"""BBot Console App."""
import os
import sys
from bbot.core import create_bot, Engine
from bbot.config import load_configuration

def chat(config: dict):
    """Chat with BBot."""
    print("\nBBot Console App - Version 1.0\n")
    print("Type \"quit\" or \"bye\" to leave chat\n\n")
    bot = create_bot(config)
    while True:
        input_text = input("You: ")
        if input_text.lower() in ["quit", "bye"]:
            print("BBot: Bye!\n")
            sys.exit(0)
        request = Engine.create_request(input_text, "joe", 7, 1)
        response = bot.get_response(request)
        print(f"BBot: {response['output']['text']}")

# Load setting and start chat
CONFIG_PATH = os.path.abspath(os.path.dirname(__file__) \
    + "../../../instance")
CONFIG_SETTINGS = load_configuration(CONFIG_PATH, "BBOT_ENV")
chat(CONFIG_SETTINGS)
