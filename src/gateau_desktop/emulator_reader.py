import asyncio
import logging
from abc import ABC, abstractmethod
from asyncio.streams import StreamReader, StreamWriter
from typing import Awaitable, Callable, Dict, List

from pydantic import BaseModel, Field

from gateau_desktop.environment import GATEAU_SOCKET_PORT

logger = logging.getLogger(__name__)

STREAM_READ_BYTES = 1024


class Byte(BaseModel):
    #: Location in memory
    location: int

    #: Value of the byte
    value: int


class RAM(BaseModel):
    #: The frame count the RAM values correspond to
    frame: int

    #: RAM data
    data: List[Byte]


class EmulatorListener(BaseModel, ABC):

    #: Callback function to invoke when a new frame of RAM is received
    on_ram_frame: Callable[[RAM], Awaitable[None]]

    @abstractmethod
    async def start(self):
        """
        Start listening to the emulator, invoking the callback when a new frame
        of RAM is read (not necessarily in order).
        """

    @abstractmethod
    async def stop(self):
        """
        Stop listening to the emulator,
        """


class SocketListener(EmulatorListener):
    """
    An emulator listener built using sockets
    """
    class Config:
        arbitrary_types_allowed = True

    #: Whether or not the socket server should keep reading.
    listener_tasks: Dict[str, asyncio.Task] = Field(default_factory=dict)

    def _connection_callback(self, reader: StreamReader, writer: StreamWriter):
        """
        Connection handler for getting data from the emulator
        """
        peername = str(writer.get_extra_info("peername"))
        logger.info(f"{peername!r} connected.")

        loop = asyncio.get_event_loop()

        async def listen(reader: StreamReader, writer: StreamWriter):
            logger.info("Starting to listen for RAM messages.")

            while True:
                # Read a whole frame - these are separeted by EOFs.
                data = await reader.read()
                ram_data = RAM.parse_raw(data)
                logger.info(f"Processing RAM for frame {ram_data.frame!r}")

                #: Fire a task for handling the RAM frame and forget about it.
                loop.create_task(self.on_ram_frame(ram_data))
                await asyncio.sleep(0)

        def cleanup(future: asyncio.Future):
            future.result()
            logger.info(f"Removing listener for {peername}")
            del self.listener_tasks[peername]

        # Create listener task.
        self.listener_tasks[peername] = loop.create_task(
            listen(reader=reader, writer=writer)
        )
        self.listener_tasks[peername].add_done_callback(cleanup)

    async def start(self):
        """
        Start listening to the emulator, invoking the callback when a new frame
        of RAM is read (not necessarily in order).
        """
        await asyncio.start_server(
            self._connection_callback,
            host="127.0.0.1",
            port=GATEAU_SOCKET_PORT,
        )

    async def stop(self):
        """
        Stop listening to the emulator,
        """
        for peername, task in self.listener_tasks.items():
            logger.info(f"Stopping handler task for {peername}")
            task.cancel()
