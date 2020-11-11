# -*- coding: utf-8 -*-

import argparse
import asyncio
import logging
import sys

from . import client
from . import utils


async def run(host, port, wait_timeout=None):
    cli = client.TMateClient(host, port)
    await cli.connect()
    await cli.handshake()
    await cli.serve(wait_timeout=wait_timeout)


def main():
    parser = argparse.ArgumentParser(
        prog="tmate", description="tmate cmdline tool implemented by python."
    )
    parser.add_argument("-f", help="set the config file path")
    parser.add_argument("--host", help="tmate server host", default="ssh.tmate.io")
    parser.add_argument("--port", help="tmate server port", type=int, default=22)
    parser.add_argument(
        "--wait-timeout", help="timeout wait for client", type=float, default=0
    )

    args = parser.parse_args()

    if sys.platform == "win32":
        utils.enable_ansi_code()
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    utils.logger.setLevel(logging.DEBUG)
    utils.logger.propagate = 0
    utils.logger.addHandler(handler)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(args.host, args.port, args.wait_timeout))
    loop.close()


if __name__ == "__main__":
    sys.exit(main())
