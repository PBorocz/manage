"""'Manage' primary entry point."""
import sys
import argparse

from dotenv import load_dotenv
from rich import print

from dispatch import dispatch
from setup import setup
from utilities import run

load_dotenv(verbose=True)

# Run our own setup steps, reading/validating the recipe file and getting some core environment information etc.
configuration, recipes = setup()

# Handle arg(s)
keys = [key for key in recipes.keys() if not key.startswith("__")]
targets_available = ', '.join(sorted(keys))
parser = argparse.ArgumentParser()
parser.add_argument(
    "target",
    type=str,
    help=f"Please specify a target to run from: {targets_available}",
    nargs="?",
    default=None
)
args = parser.parse_args()
if not vars(args) or not args.target:
    parser.print_help()
    sys.exit(0)

# Validate requested target
if args.target.casefold() not in recipes:
    print(f"Sorry, {args.target} is not a valid target, please check against manage.toml.")
    sys.exit(1)

try:
    dispatch(configuration, recipes, args.target)
    print("\n[green]Done!")
except (KeyboardInterrupt, EOFError):
    sys.exit(0)
