from typing import Callable
import pytest

from gateau_desktop.emulator_reader import RAM, SocketListener
import socket

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
    listener = SocketListener(on_ram_frame=ram_log.on_ram_frame)

    try:
        await listener.start()
        yield listener
    finally:
        await listener.stop()


@pytest.fixture
def send_ram():
    """
    Create a client that can post messages to a running socket listener.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        def send_ram(ram: RAM):
            encoded = ram.json().encode("utf-8")

            s.connect(("127.0.0.1", GATEAU_SOCKET_PORT))
            s.sendall(encoded)
            s.close()

        yield send_ram
