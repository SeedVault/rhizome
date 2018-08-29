"""BBot Console App."""
import os
import sys
from bbot.core import create_bot, ChatbotEngine
from bbot.config import load_configuration

def chat(config: dict):
    """Chat with BBot."""
    
    print("\nBBot Console App - Version 1.0\n")
    
    if len(sys.argv) <= 2:
        print("Usage: make console user_id bot_id org_id\n")
        sys.exit(255)
    
    print("Type \"quit\" or \"bye\" to leave chat\n\n")
    
    user_id, bot_id, org_id = sys.argv[2:]
    
    bot = create_bot(config)
    while True:
        input_text = input("You: ")
        if input_text.lower() in ["quit", "bye"]:
            print("BBot: Bye!\n")
            sys.exit(0)
        request = ChatbotEngine.create_request({'text': input_text}, user_id, bot_id, org_id)
        response = bot.get_response(request)        
        print(f"BBot: {response['text'][0]}")

# Load setting and start chat
CONFIG_PATH = os.path.abspath(os.path.dirname(__file__) \
    + "../../../instance")
CONFIG_SETTINGS = load_configuration(CONFIG_PATH, "BBOT_ENV")
chat(CONFIG_SETTINGS)
