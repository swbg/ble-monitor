import argparse
import logging

from ble_monitor.config import config
from ble_monitor.db import add_devices, create_tables
from ble_monitor.monitor import start_monitor
from ble_monitor.utils import set_up_logging


def create():
    create_tables(drop=True)
    add_devices()


def start():
    start_monitor()


def run():
    parser = argparse.ArgumentParser(description="BLE Monitor")
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        type=str,
        help="Path to config file",
    )
    parser.add_argument(
        "action",
        nargs="?",
        choices=["start", "create"],
        default="start",
        help="Action to perform",
    )
    args = parser.parse_args()

    config.set_config(args.config)

    set_up_logging(logging.INFO, config.get("logging_file_path"))

    if args.action == "create":
        create()
    elif args.action == "start":
        start()


if __name__ == "__main__":
    run()
