import asyncio
import socket

import pytest

from gateau_desktop.emulator_reader import RAM, SocketListener
from gateau_desktop.environment import GATEAU_SOCKET_PORT


class RAMLog:
    def __init__(self):
        self.messages = []

    async def on_ram_frame(self, ram: RAM):
        self.messages.append(ram)


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
async def send_ram(socket_listener: SocketListener):
    """
    Return a function that can post messages to a running socket listener.
    The function will ensure the task is received and processed before completing.
    """

    async def send(ram: RAM):
        original_tasks = len(socket_listener.processing_tasks)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            encoded = ram.json().encode("utf-8")

            s.connect(("127.0.0.1", GATEAU_SOCKET_PORT))
            s.sendall(encoded)
            s.close()

            while len(socket_listener.processing_tasks) == original_tasks:
                # Wait for the task to appear on the processor.
                await asyncio.sleep(0)

            await socket_listener._process_all()

    return send
