import asyncio

from gateau_desktop.emulator_listener import RAM, SocketListener


async def handle_ram(ram: RAM):
    (pokemon_1,) = [b.value for b in ram.ram_data if b.location == 0xD164]
    print(f"Frame {ram.frame} | Slot 1: {pokemon_1}")
    await asyncio.sleep(0)


async def run_server():
    async with SocketListener(on_ram_frame=handle_ram):
        while True:
            await asyncio.sleep(0)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run_server())
    loop.run_forever()
