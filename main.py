import os, sys
# Ensure src directory is on path for imports
sys.path.append(os.path.dirname(__file__))
from game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()