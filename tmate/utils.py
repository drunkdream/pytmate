# -*- coding: utf-8 -*-

import asyncio
import ctypes
import logging
import os

logger = logging.getLogger("pytmate")

KEYC_BASE = 0x100000000000


class EnumTMateDaemonInMessageType(object):
    TMATE_IN_NOTIFY = 0
    TMATE_IN_LEGACY_PANE_KEY = 1
    TMATE_IN_RESIZE = 2
    TMATE_IN_EXEC_CMD_STR = 3
    TMATE_IN_SET_ENV = 4
    TMATE_IN_READY = 5
    TMATE_IN_PANE_KEY = 6
    TMATE_IN_EXEC_CMD = 7


class EnumTMateDaemonOutMessageType(object):
    TMATE_OUT_HEADER = 0
    TMATE_OUT_SYNC_LAYOUT = 1
    TMATE_OUT_PTY_DATA = 2
    TMATE_OUT_EXEC_CMD_STR = 3
    TMATE_OUT_FAILED_CMD = 4
    TMATE_OUT_STATUS = 5
    TMATE_OUT_SYNC_COPY_MODE = 6
    TMATE_OUT_WRITE_COPY_MODE = 7
    TMATE_OUT_FIN = 8
    TMATE_OUT_READY = 9
    TMATE_OUT_RECONNECT = 10
    TMATE_OUT_SNAPSHOT = 11
    TMATE_OUT_EXEC_CMD = 12
    TMATE_OUT_UNAME = 13


class AsyncFileDescriptor(object):
    """Async File Descriptor"""

    def __init__(self, fd):
        self._loop = asyncio.get_event_loop()
        self._fd = fd
        self._event = asyncio.Event()
        self._buffer = b""
        self._loop.add_reader(self._fd, self.read_callback)
        self._closed = False

    def close(self):
        self._loop.remove_reader(self._fd)

    async def read(self, bytes=4096):
        await self._event.wait()
        self._event.clear()
        buffer = self._buffer
        self._buffer = b""
        return buffer

    def write(self, buffer):
        os.write(self._fd, buffer)

    def read_callback(self, *args):
        try:
            buffer = os.read(self._fd, 4096)
        except OSError:
            self.close()
            self._closed = True
            self._event.set()
            return

        self._buffer += buffer
        self._event.set()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_trackback):
        self.close()
        self._closed = True


class Process(object):
    def __init__(self, pid):
        self._pid = pid
        self._returncode = None
        safe_ensure_future(self._wait_for_exit())

    @property
    def returncode(self):
        return self._returncode

    async def _wait_for_exit(self):
        while True:
            try:
                pid, returncode = os.waitpid(self._pid, os.WNOHANG)
            except ChildProcessError:
                logger.warn(
                    "[%s] Process %d already exited" % (self.__class__.__name__, pid)
                )
                self._returncode = -1
                break

            if not pid:
                await asyncio.sleep(0.01)
            else:
                self._returncode = returncode
                break


def safe_ensure_future(coro, loop=None):
    loop = loop or asyncio.get_event_loop()
    fut = loop.create_future()

    async def _wrap():
        try:
            fut.set_result(await coro)
        except Exception as e:
            fut.set_exception(e)

    asyncio.ensure_future(_wrap())
    return fut


def ensure_unicode(s):
    if isinstance(s, bytes):
        s = s.decode()
    return s


def enable_ansi_code():
    result = ctypes.windll.kernel32.SetConsoleMode(
        ctypes.windll.kernel32.GetStdHandle(-11), 7
    )
    return result == 1
