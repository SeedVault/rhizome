"""
BBot Console App.

run this with: BBOT_ENV=development make console joe 5b9add84e2e290380e4fd3cf 1 nodebug

"""
import os
import sys
import logging.config
from bbot.core import create_bot, ChatbotEngine, Plugin
from bbot.config import load_configuration


# Load setting and start chat
config_path = os.path.abspath(os.path.dirname(__file__) + "../../../instance")
config = load_configuration(config_path, "BBOT_ENV")
c_config = config["channel_console"]
console = Plugin.load_plugin(c_config)
logging.config.dictConfig(config['logging'])
logger = logging.getLogger("channel_console")


print("\nBBot Console App - Version 1.0\n")

if len(sys.argv) <= 4:
    print("Usage: make console user_id bot_id org_id\n")
    sys.exit(255)

print("Type \"quit\" or \"bye\" to leave chat\n\n")

user_id, bot_id, org_id, debug = sys.argv[2:]


dotbotContainer = console.dotdb.find_dotbot_by_idname(bot_id)
if not dotbotContainer:
    raise Exception('Couldn\'t find the bot')

bot = create_bot(config, dotbotContainer.dotbot)
while True:
    input_text = input("You: ")
    if input_text.lower() in ["!quit", "!bye"]:
        print("BBot: Bye!\n")
        sys.exit(0)
    request = ChatbotEngine.create_request({'text': input_text}, user_id, bot_id, org_id)
    response = bot.get_response(request)

    if debug == 'debug':
        print(f"Debug: {response}")

    for r in response['output']:
        for text in r.get('text', []):
            print(f"BBot: {text}")



            




