from qwen_agent.gui import WebUI
from app.core.agent import bot

def app_gui():
    WebUI(bot).run()


if __name__ == '__main__':
    # test()
    app_gui()