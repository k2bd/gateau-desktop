

from typing import Callable

import pytest
from gateau_desktop.emulator_reader import RAM, Byte, SocketListener
from tests.conftest import RAMLog


@pytest.mark.asyncio
async def test_send_ram_message(ram_log: RAMLog, socket_listener: SocketListener, send_ram: Callable[[RAM], None]):
    ram = RAM(
        frame=10,
        data=[
            Byte(location=123, value=456),
            Byte(location=234, value=567),
        ]
    )
    send_ram(ram)

    assert ram_log.messages == [ram]
