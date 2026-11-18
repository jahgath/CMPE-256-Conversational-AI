"""Terminal chat:  python cli.py   (or: python cli.py "one-shot question")"""
import sys
from econ_chat.agent import Agent

a = Agent()
if len(sys.argv) > 1:
    print(a.ask(" ".join(sys.argv[1:]))); sys.exit()
print(f"FRED GDP & Core CPI assistant — mode: {a.mode}\nType 'quit' to exit.")
while True:
    try:
        q = input("\nyou> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if q.lower() in ("quit", "exit"):
        break
    if q:
        print("\nbot>", a.ask(q))
