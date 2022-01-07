from typing import Awaitable, Callable

import pytest

from gateau_desktop.emulator_listener import RAM, Byte, SocketListener
from tests.conftest import RAMLog


@pytest.mark.asyncio
async def test_send_ram_message(
    ram_log: RAMLog,
    socket_listener: SocketListener,
    send_ram: Callable[[RAM], Awaitable[None]],
):
    ram = RAM(
        frame=10,
        ram_data=[
            Byte(location=123, value=456),
            Byte(location=234, value=567),
        ],
    )

    await send_ram(ram)

    assert ram_log.on_ram_frame_msgs == [ram]


@pytest.mark.asyncio
async def test_send_multiple(
    ram_log: RAMLog,
    socket_listener: SocketListener,
    send_ram: Callable[[RAM], Awaitable[None]],
):
    ram1 = RAM(
        frame=10,
        ram_data=[
            Byte(location=123, value=456),
            Byte(location=234, value=567),
        ],
    )

    ram2 = RAM(
        frame=11,
        ram_data=[
            Byte(location=123, value=222),
            Byte(location=234, value=333),
        ],
    )

    await send_ram(ram1)
    await send_ram(ram2)

    assert sorted(ram_log.on_ram_frame_msgs, key=lambda r: r.frame) == [ram1, ram2]
