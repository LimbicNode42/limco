import os
from dotenv import load_dotenv
from .graph import create_recovery_graph

# Load environment variables from .env file
load_dotenv()

app = create_recovery_graph()


def main():
    """
    Main entry point for the data recovery agent.
    """
    initial_state = {}
    for event in app.stream(initial_state):
        print(event)


if __name__ == "__main__":
    main()
