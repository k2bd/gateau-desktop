from typing import Awaitable, Callable

import pytest

from gateau_desktop.emulator_listener import RAM, Byte
from gateau_desktop.ram_monitor import RamChangeInfo, RamEvent, RamMonitor
from tests.conftest import RAMLog


@pytest.mark.asyncio
async def test_ram_monitor_simple_change(
    ram_log: RAMLog,
    socket_ram_monitor: RamMonitor,
    send_ram: Callable[[RAM], Awaitable[None]],
):
    """
    Initial frame is correctly recorded, and a simple change works too.
    Old frame data coming in doesn't register a change.
    """
    ram_1 = RAM(
        frame=10,
        ram_data=[
            Byte(location=1, value=1),
            Byte(location=2, value=2),
            Byte(location=3, value=3),
            Byte(location=4, value=4),
            Byte(location=5, value=5),
            Byte(location=6, value=6),
            Byte(location=7, value=7),
            Byte(location=8, value=8),
            Byte(location=9, value=9),
            Byte(location=10, value=10),
        ],
    )
    ram_2 = RAM(
        frame=20,
        ram_data=[
            Byte(location=1, value=1),
            Byte(location=2, value=2),
            Byte(location=3, value=33),  # Subscribed change
            Byte(location=4, value=4),
            Byte(location=5, value=55),  # Subscribed change
            Byte(location=6, value=66),  # Non-subscribed change
            Byte(location=7, value=7),
            Byte(location=8, value=8),
            Byte(location=9, value=9),
            Byte(location=10, value=10),
        ],
    )
    ram_3 = RAM(
        frame=15,  # Previous frame, should be ignored
        ram_data=[
            Byte(location=1, value=1),
            Byte(location=2, value=2),
            Byte(location=3, value=300),  # Subscribed change
            Byte(location=4, value=4),
            Byte(location=5, value=500),  # Subscribed change
            Byte(location=6, value=600),  # Non-subscribed change
            Byte(location=7, value=7),
            Byte(location=8, value=8),
            Byte(location=9, value=9),
            Byte(location=10, value=10),
        ],
    )

    await send_ram(ram_1)

    expected_initial_events = RamChangeInfo(
        frame=10,
        old_frame=None,
        events=[RamEvent(location=i, old=None, new=i) for i in [1, 2, 3, 5, 8]],
    )

    assert ram_log.on_ram_change_msgs == [expected_initial_events]

    await send_ram(ram_2)

    expected_changes = RamChangeInfo(
        frame=20,
        old_frame=10,
        events=[
            RamEvent(location=3, new=33, old=3),
            RamEvent(location=5, new=55, old=5),
        ],
    )

    assert ram_log.on_ram_change_msgs == [expected_initial_events, expected_changes]

    # Old data processed
    await send_ram(ram_3)

    # No change
    assert ram_log.on_ram_change_msgs == [expected_initial_events, expected_changes]
