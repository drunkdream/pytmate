# -*- coding: utf-8 -*-

import asyncio
import os
import platform
import sys
import time

import asyncssh
import msgpack

from . import VERSION
from . import shell
from . import utils


KEY_BINDINGS = [
    ("C-b", "send-prefix"),
    ("C-o", "rotate-window"),
    ("C-z", "suspend-client"),
    ("Space", "next-layout"),
    ("!", "break-pane"),
    ('"', "split-window"),
    ("#", "list-buffers"),
    ("$", "command-prompt", "-I#S", "rename-session '%%'"),
    ("%", "split-window", "-h"),
    (
        "&",
        "confirm-before",
        "-pkill-window #W? (y/n)",
        "kill-window",
    ),
    ("'", "command-prompt", "-pindex", "select-window -t ':%%'"),
    ("(", "switch-client", "-p"),
    (")", "switch-client", "-n"),
    (",", "command-prompt", "-I#W", "rename-window '%%'"),
    ("-", "delete-buffer"),
    (".", "command-prompt", "move-window -t '%%'"),
    ("0", "select-window", "-t:=0"),
    ("1", "select-window", "-t:=1"),
    ("2", "select-window", "-t:=2"),
    ("3", "select-window", "-t:=3"),
    ("4", "select-window", "-t:=4"),
    ("5", "select-window", "-t:=5"),
    ("6", "select-window", "-t:=6"),
    ("7", "select-window", "-t:=7"),
    ("8", "select-window", "-t:=8"),
    ("9", "select-window", "-t:=9"),
    (":", "command-prompt"),
    (";", "last-pane"),
    ("=", "choose-buffer"),
    ("?", "list-keys"),
    ("D", "choose-client"),
    ("L", "switch-client", "-l"),
    ("M", "select-pane", "-M"),
    ("[", "copy-mode"),
    ("]", "paste-buffer"),
    ("c", "new-window"),
    ("d", "detach-client"),
    ("f", "command-prompt", "find-window '%%'"),
    ("i", "display-message"),
    ("l", "last-window"),
    ("m", "select-pane", "-m"),
    ("n", "next-window"),
    ("o", "select-pane", "-t:.+"),
    ("p", "previous-window"),
    ("q", "display-panes"),
    ("r", "refresh-client"),
    ("s", "choose-tree"),
    ("t", "clock-mode"),
    ("w", "choose-window"),
    ("x", "confirm-before", "-pkill-pane #P? (y/n)", "kill-pane"),
    ("z", "resize-pane", "-Z"),
    ("{", "swap-pane", "-U"),
    ("}", "swap-pane", "-D"),
    ("~", "show-messages"),
    ("PPage", "copy-mode", "-u"),
    ("-r", "Up", "select-pane", "-U"),
    ("-r", "Down", "select-pane", "-D"),
    ("-r", "Left", "select-pane", "-L"),
    ("-r", "Right", "select-pane", "-R"),
    ("M-1", "select-layout", "even-horizontal"),
    ("M-2", "select-layout", "even-vertical"),
    ("M-3", "select-layout", "main-horizontal"),
    ("M-4", "select-layout", "main-vertical"),
    ("M-5", "select-layout", "tiled"),
    ("M-n", "next-window", "-a"),
    ("M-o", "rotate-window", "-D"),
    ("M-p", "previous-window", "-a"),
    ("-r", "M-Up", "resize-pane", "-U", "5"),
    ("-r", "M-Down", "resize-pane", "-D", "5"),
    ("-r", "M-Left", "resize-pane", "-L", "5"),
    ("-r", "M-Right", "resize-pane", "-R", "5"),
    ("-r", "C-Up", "resize-pane", "-U"),
    ("-r", "C-Down", "resize-pane", "-D"),
    ("-r", "C-Left", "resize-pane", "-L"),
    ("-r", "C-Right", "resize-pane", "-R"),
    (
        "-n",
        "MouseDown1Pane",
        "select-pane",
        "-t=;",
        "send-keys",
        "-M",
    ),
    ("-n", "MouseDrag1Border", "resize-pane", "-M"),
    ("-n", "MouseDown1Status", "select-window", "-t="),
    ("-n", "WheelDownStatus", "next-window"),
    ("-n", "WheelUpStatus", "previous-window"),
    (
        "-n",
        "MouseDrag1Pane",
        "if",
        "-Ft=",
        "#{mouse_any_flag}",
        'if -Ft= "#{pane_in_mode}" "copy-mode -M" "send-keys -M"',
        "copy-mode -M",
    ),
    (
        "-n",
        "MouseDown3Pane",
        "if-shell",
        "-Ft=",
        "#{mouse_any_flag}",
        "select-pane -t=; send-keys -M",
        "select-pane -mt=",
    ),
    (
        "-n",
        "WheelUpPane",
        "if-shell",
        "-Ft=",
        "#{mouse_any_flag}",
        "send-keys -M",
        'if -Ft= "#{pane_in_mode}" "send-keys -M" "copy-mode -et="',
    ),
]


class TMateClient(object):
    """TMate Client"""

    def __init__(self, host, port, username="tmate"):
        self._host = host
        self._port = port
        self._username = username
        self._size = (80, 23)
        self._channel_reader = None
        self._channel_writer = None
        self._ready = False
        self._shell = None
        self._stdin_buffer = b""

    async def connect(self):
        utils.logger.info(
            "[%s] Connect SSH server %s:%d..."
            % (self.__class__.__name__, self._host, self._port)
        )
        options = {
            "known_hosts": None,
            "host": self._host,
            "port": self._port,
            "username": self._username,
        }
        options = asyncssh.SSHClientConnectionOptions(**options)
        ssh_conn = await asyncssh.connect(
            self._host, self._port, known_hosts=None, username=self._username
        )
        self._channel_writer, self._channel_reader, _ = await ssh_conn.open_session(
            subsystem="tmate", env=(), send_env=(), encoding=None
        )
        ssh_conn.set_keepalive(300, 3)
        return True

    async def handshake(self):
        messages = [
            [utils.EnumTMateDaemonOutMessageType.TMATE_OUT_HEADER, 6, VERSION],
            [
                utils.EnumTMateDaemonOutMessageType.TMATE_OUT_EXEC_CMD,
                "set-option",
                "-g",
                "status-keys",
                "emacs",
            ],
            [
                utils.EnumTMateDaemonOutMessageType.TMATE_OUT_EXEC_CMD,
                "set-window-option",
                "-g",
                "status-keys",
                "emacs",
            ],
            [
                utils.EnumTMateDaemonOutMessageType.TMATE_OUT_EXEC_CMD,
                "set-option",
                "tmate-set",
                "foreground=true",
            ],
            [
                utils.EnumTMateDaemonOutMessageType.TMATE_OUT_UNAME,
                platform.system(),
                platform.node(),
                platform.release(),
                platform.version(),
                platform.processor(),
            ],
        ]
        for it in KEY_BINDINGS:
            message = [
                utils.EnumTMateDaemonOutMessageType.TMATE_OUT_EXEC_CMD,
                "bind-key",
            ]
            message.extend(it)
            messages.append(message)
        messages.append([utils.EnumTMateDaemonOutMessageType.TMATE_OUT_READY])
        buffer = b""
        for it in messages:
            buffer += msgpack.dumps(it)
        self._channel_writer.write(buffer)
        self.update_layout(self._size)

    async def serve(self, wait_timeout=None, timeout=None):
        time0 = time.time()
        while timeout is None or time.time() - time0 < timeout:
            if not self._shell and wait_timeout and time.time() - time0 >= wait_timeout:
                utils.logger.warn(
                    "[%s] Wait for client timeout" % self.__class__.__name__
                )
                return
            try:
                buffer = await asyncio.wait_for(
                    self._channel_reader.read(4096), timeout=1
                )
            except asyncio.TimeoutError:
                continue
            except asyncssh.ConnectionLost:
                break
            unpacker = msgpack.Unpacker()
            unpacker.feed(buffer)
            for msg in unpacker:
                self.process_message_in(msg)
        utils.logger.info("[%s] TMate client exit" % self.__class__.__name__)

    async def spawn_shell(self, size):
        utils.logger.info(
            "[%s] Spawn new shell (%d, %d)"
            % (self.__class__.__name__, size[0], size[1])
        )
        self._shell = shell.Shell(size)
        proc, _, _, _ = await self._shell.create()
        tasks = [None]
        if self._shell.stderr:
            tasks.append(None)
        while proc.returncode is None:
            if tasks[0] is None:
                tasks[0] = utils.safe_ensure_future(self._shell.stdout.read(4096))
            if self._shell.stderr and tasks[1] is None:
                tasks[1] = utils.safe_ensure_future(self._shell.stderr.read(4096))

            done_tasks, _ = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )

            for task in done_tasks:
                index = tasks.index(task)
                assert index >= 0
                tasks[index] = None
                buffer = task.result()
                if not buffer:
                    await asyncio.sleep(0.01)
                    break

                message = [
                    utils.EnumTMateDaemonOutMessageType.TMATE_OUT_PTY_DATA,
                    0,
                    buffer,
                ]
                self.send_message(message)
        utils.logger.warn("[%s] Shell process exit" % self.__class__.__name__)
        self._shell = None
        message = [
            utils.EnumTMateDaemonOutMessageType.TMATE_OUT_PTY_DATA,
            0,
            b"Please press `<ENTER>~.` to exit.\r\n",
        ]
        self.send_message(message)

    def process_message_in(self, message):
        if message[0] == utils.EnumTMateDaemonInMessageType.TMATE_IN_NOTIFY:
            utils.logger.info("[Notify] %s" % utils.ensure_unicode(message[1]))
        elif message[0] == utils.EnumTMateDaemonInMessageType.TMATE_IN_SET_ENV:
            os.environ[utils.ensure_unicode(message[1])] = utils.ensure_unicode(
                message[2]
            )
        elif message[0] == utils.EnumTMateDaemonInMessageType.TMATE_IN_READY:
            self._ready = True
        elif message[0] == utils.EnumTMateDaemonInMessageType.TMATE_IN_RESIZE:
            size = message[1:]
            utils.logger.info(
                "[%s] Window size changed to %d, %d"
                % (self.__class__.__name__, size[0], size[1])
            )
            if size[0] <= 0 or size[1] <= 0:
                return
            if self._shell is None:
                utils.safe_ensure_future(self.spawn_shell(size))
            else:
                self._shell.resize(size)
            self.update_layout(size)
        elif message[0] == utils.EnumTMateDaemonInMessageType.TMATE_IN_PANE_KEY:
            keycode = message[2]
            buffer = self._stdin_buffer
            self._stdin_buffer = b""
            if keycode < 256:
                buffer += chr(keycode).encode()
                if sys.platform == "win32" and buffer.startswith(b"\x1b"):
                    # ensure send ansi code together
                    for it in (
                        b"\x1b[A",
                        b"\x1b[B",
                        b"\x1b[C",
                        b"\x1b[D",
                    ):
                        if buffer == it:
                            break
                    else:
                        if len(buffer) > 3:
                            utils.logger.info(
                                "[%s] Wait for stdin ansi code: %r"
                                % (self.__class__.__name__, buffer)
                            )
                        self._stdin_buffer = buffer
                        return
            elif keycode & utils.KEYC_BASE:
                keycode %= utils.KEYC_BASE
                key = chr(keycode)
                if key in ("A", "B"):
                    buffer = ("\x1b[%s" % key).encode()
                elif key == "C":
                    buffer = b"\x1b[D"
                elif key == "D":
                    buffer = b"\x1b[C"
                elif key == "-":
                    buffer = b"\x08"
                else:
                    raise NotImplementedError(key)
            else:
                utils.logger.warn(
                    "[%s] Unknown keycode 0x%x" % (self.__class__.__name__, keycode)
                )
                return

            if self._shell:
                self._shell.stdin.write(buffer)
            else:
                utils.logger.warn(
                    "[%s] Received %r after shell process exit"
                    % (self.__class__.__name__, buffer)
                )
        else:
            raise NotImplementedError(message)

    def send_message(self, message):
        buffer = msgpack.dumps(message)
        self._channel_writer.write(buffer)

    def get_default_shell(self):
        if sys.platform == "win32":
            return "cmd.exe"
        else:
            return os.environ.get("SHELL", "sh")

    def update_layout(self, size):
        message = [
            utils.EnumTMateDaemonOutMessageType.TMATE_OUT_SYNC_LAYOUT,
            size[0],
            size[1],
            [[0, self.get_default_shell(), [[0, size[0], size[1], 0, 0]], 0]],
            0,
        ]
        self.send_message(message)
