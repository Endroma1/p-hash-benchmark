"""
CLI tool for p-hash
"""
import argparse
import httpx
from .config import Config

CONFIG = Config.from_env()

def main():
    parser = argparse.ArgumentParser(prog="P-Hash", description="CLI tool for p-hash benchmarking tool")

    parser.add_argument('start', help="Starts the loading, modifying, and hashing")
    parser.add_argument('-c', '--component', help="Specifies component to run")

    args = parser.parse_args()

    if args.start:
        if args.component == "match":
            start_match()

def start_components():
    with httpx.Client() as client:
        resp = client.post(f"{CONFIG.orchestrator_url}/admin/start/all")
        print(resp.json())

def start_match():
    with httpx.Client() as client:
        resp = client.post(f"{CONFIG.orchestrator_url}/admin/start/match")
        print(resp.json())

if __name__ == "__main__":
    main()
