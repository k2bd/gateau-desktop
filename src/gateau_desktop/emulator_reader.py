import asyncio
import json
import logging
import sys
from abc import ABC, abstractmethod
from asyncio.base_events import Server
from asyncio.streams import StreamReader, StreamWriter
from typing import Awaitable, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from gateau_desktop.environment import GATEAU_SOCKET_PORT

logger = logging.getLogger(__name__)


class Byte(BaseModel):
    #: Location in memory
    location: int

    #: Value of the byte
    value: int


class RAM(BaseModel):
    #: The frame count the RAM values correspond to
    frame: int

    #: RAM data
    ram_data: List[Byte]


@runtime_checkable
class OnRamFrame(Protocol):
    def __call__(self, ram: RAM) -> Awaitable[None]:
        ...


class EmulatorListener(BaseModel, ABC):
    class Config:
        arbitrary_types_allowed = True

    #: Callback function to invoke when a new frame of RAM is received
    on_ram_frame: OnRamFrame

    @abstractmethod
    async def __aenter__(self):
        """
        Start listening to the emulator, invoking the callback when a new frame
        of RAM is read (not necessarily in order).
        """

    @abstractmethod
    async def __aexit__(self, *err):
        """
        Stop listening to the emulator,
        """


class SocketListener(EmulatorListener):
    """
    An emulator listener built using sockets
    """

    #: Whether or not the socket server should keep reading.
    listener_tasks: Dict[str, asyncio.Task] = Field(default_factory=dict)

    #: RAM processing tasks (for internal tracking)
    processing_tasks: List[asyncio.Task] = Field(default_factory=list)

    #: Cleaner task to periodically trim the processing task list
    cleaner_task: Optional[asyncio.Task] = None

    #: Socket server
    server: Optional[Server] = None

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
                # Read a RAM frame - defined by 8 bytes with the message
                # length, then the message itself.
                len_data = await reader.read(8)

                if not len_data:
                    logger.info("Got EOF, exiting")
                    break

                message_len: int = int.from_bytes(len_data, sys.byteorder)
                ram_data = await reader.readexactly(message_len)

                ram_frame = RAM.parse_obj(json.loads(ram_data.decode("utf-8")))
                logger.info(f"Processing RAM for frame {ram_frame.frame!r}")

                #: Fire a task for handling the RAM frame
                task = loop.create_task(self.on_ram_frame(ram_frame))
                self.processing_tasks.append(task)

        # Create listener task.
        self.listener_tasks[peername] = loop.create_task(
            listen(reader=reader, writer=writer)
        )

    async def __aenter__(self):
        """
        Start listening to the emulator, invoking the callback when a new frame
        of RAM is read (not necessarily in order).
        """
        server = await asyncio.start_server(
            self._connection_callback,
            host="127.0.0.1",
            port=GATEAU_SOCKET_PORT,
        )
        self.server = server

        loop = asyncio.get_event_loop()
        self.cleaner_task = loop.create_task(self._clean_processing_tasks())

        return self

    async def __aexit__(self, *err):
        """
        Stop listening to the emulator
        """
        await self._process_all()

        for peername, task in self.listener_tasks.items():
            logger.info(f"Stopping handler task for {peername}")
            task.cancel()
        self.listener_tasks = {}

        if self.cleaner_task:
            self.cleaner_task.cancel()
            self.cleaner_task = None

        if self.server:
            self.server.close()
            self.server = None

    async def _clean_processing_tasks(self):
        """
        Helper method to periodically clean up the processing task list so it
        doesn't grow indefinitely.
        """
        while True:
            self.processing_tasks = [
                task for task in self.processing_tasks if not task.done()
            ]
            await asyncio.sleep(10)

    async def _process_all(self):
        """
        Process remaining tasks
        """
        for task in self.processing_tasks:
            if not task.done():
                await task
