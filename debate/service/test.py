from agent.DebateManager import DebateManager
from config import Settings


if __name__ == "__main__":
    config = Settings()
    debate_manager = DebateManager(config)
    input = "AI是不是一个好东西？"
    content = debate_manager.run(input)
