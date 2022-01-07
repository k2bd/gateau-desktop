import asyncio
import socket
import sys

import pytest

from gateau_desktop.emulator_listener import RAM, SocketListener
from gateau_desktop.environment import GATEAU_SOCKET_PORT
from gateau_desktop.ram_monitor import RamChangeInfo, RamMonitor


class RAMLog:
    def __init__(self):
        self.on_ram_frame_msgs = []
        self.on_ram_change_msgs = []

    async def on_ram_frame(self, ram: RAM):
        self.on_ram_frame_msgs.append(ram)

    async def on_ram_change(self, info: RamChangeInfo):
        self.on_ram_change_msgs.append(info)


@pytest.fixture
def ram_log():
    """
    Provide a class that lets an EmulatorListener post RAM messages, and
    stores them.
    """
    return RAMLog()


@pytest.fixture
async def socket_listener(ram_log: RAMLog):
    """
    Yield a running socket listener
    """
    async with SocketListener(on_ram_frame=ram_log.on_ram_frame) as listener:
        yield listener


@pytest.fixture
def socket_ram_monitor(ram_log: RAMLog, socket_listener: SocketListener):
    """
    Subscribe to changes in RAM frames sent down a socket.
    The monitor is subscribed to changes in bytes 1, 2, 3, 5, and 8
    """
    monitor = RamMonitor(
        subscription=[1, 2, 3, 5, 8],
        on_ram_change=ram_log.on_ram_change,
    )
    socket_listener.on_ram_frame = monitor.ram_frame_handler

    return monitor


@pytest.fixture
async def send_ram(socket_listener: SocketListener):
    """
    Return a function that can post messages to a running socket listener.
    The function will ensure the task is received and processed before completing.
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(("127.0.0.1", GATEAU_SOCKET_PORT))

        async def send(ram: RAM):
            original_tasks = len(socket_listener.processing_tasks)
            encoded = ram.json().encode("utf-8")
            len_byte = len(encoded).to_bytes(8, sys.byteorder)

            s.sendall(len_byte + encoded)

            while len(socket_listener.processing_tasks) == original_tasks:
                # Wait for the task to appear on the processor.
                await asyncio.sleep(0)

            await socket_listener._process_all()

        yield send
