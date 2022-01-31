import asyncio

from gateau_desktop.emulator_listener import SocketListener
from gateau_desktop.ram_monitor import RamChangeInfo, RamMonitor
import requests


async def handle_change(info: RamChangeInfo):
    requests.post(
        "http://127.0.0.1:8011/game/aaaa/ramChange",
        headers={"player-id": "tempPlayer123"},
        json=info.dict(),
    )
    await asyncio.sleep(0)


async def run_server():
    subs = requests.get(
        "http://127.0.0.1:8011/game/aaaa/ramSubscriptions",
        headers={"player-id": "tempPlayer123"},
    )
    addrs = [int(addr) for addr in subs.json()["ramAddresses"]]
    print(addrs)

    monitor = RamMonitor(
        subscription=addrs,
        on_ram_change=handle_change,
    )
    async with SocketListener(on_ram_frame=monitor.ram_frame_handler):
        while True:
            await asyncio.sleep(0)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_server())
    loop.run_forever()
