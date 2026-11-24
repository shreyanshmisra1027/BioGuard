#!/usr/bin/env python3
"""
BioGuard CLI Entry Point

Run any of the BioGuard monitoring cases from a single entry point.

Usage:
    python run.py --mode hardware-test
    python run.py --mode white
    python run.py --mode yellow
    python run.py --mode yellow-lcd
    python run.py --mode yellow --no-lcd
    python run.py --mode white --lcd
"""

import argparse
import sys
import os

from bioguard.config import Config


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="BioGuard - Raspberry Pi 5 Compliance Monitoring System"
    )

    parser.add_argument(
        "--mode",
        choices=["hardware-test", "white", "yellow", "yellow-lcd"],
        default="white",
        help="Monitoring mode to run (default: white)"
    )

    parser.add_argument(
        "--lcd",
        dest="lcd",
        action="store_true",
        default=None,
        help="Enable LCD display"
    )

    parser.add_argument(
        "--no-lcd",
        dest="lcd",
        action="store_false",
        help="Disable LCD display"
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Flask server host (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Flask server port (default: 5000)"
    )

    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()

    # Route based on mode
    if args.mode == "hardware-test":
        print("Starting hardware test server...")
        from hardware_test_server import main as hw_main
        # Re-execute hardware_test_server directly
        os.system(f"python3 hardware_test_server.py")

    elif args.mode == "white":
        print("Starting white detector...")
        os.system(f"python3 white_detector.py")

    elif args.mode == "yellow":
        print("Starting yellow detector...")
        os.system(f"python3 yellow_detector.py")

    elif args.mode == "yellow-lcd":
        print("Starting yellow LCD detector...")
        os.system(f"python3 yellow_lcd_detector.py")

    else:
        print(f"Unknown mode: {args.mode}")
        sys.exit(1)


if __name__ == '__main__':
    main()