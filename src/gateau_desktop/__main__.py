import asyncio

from gateau_desktop.emulator_listener import RAM, SocketListener
from gateau_desktop.ram_monitor import RamChangeInfo, RamMonitor


async def handle_change(info: RamChangeInfo):
    slot1_event, = info.events
    print(f"Slot 1 changed from {slot1_event.old} to {slot1_event.new}")
    await asyncio.sleep(0)


async def run_server():
    monitor = RamMonitor(
        subscription=[0xD164],  # Slot 1 Pokemon
        on_ram_change=handle_change,
    )
    async with SocketListener(on_ram_frame=monitor.ram_frame_handler):
        while True:
            await asyncio.sleep(0)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_server())
    loop.run_forever()
