"""Kept for the old command name; `python main.py fetch` is the entry point now."""

import sys

from main import main

if __name__ == '__main__':
    sys.exit(main(["fetch"]))
