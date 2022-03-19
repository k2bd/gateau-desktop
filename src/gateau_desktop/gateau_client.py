from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Type

import aiohttp
from firebasil.auth import AuthClient

from gateau_desktop.emulator_listener import SocketListener
from gateau_desktop.ram_monitor import RamChangeInfo, RamMonitor

logging.basicConfig(
    format="(%(asctime)s) %(levelname)s: %(message)s",
    datefmt="%m/%d/%Y %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

CLIENT_REFRESH_INTERVAL_SECONDS = 300


@dataclass
class GateauClient:

    #: Gateau room to connect to
    room_code: str

    #: Logged in user ID token
    id_token: str

    #: Logged in user refresh token
    refresh_token: str

    #: URL of the Gateau API
    gateau_api_url: str

    #: API key of the Gateau auth app
    gateau_auth_api_key: str

    session: aiohttp.ClientSession = field(
        init=False,
        repr=False,
        hash=False,
        compare=False,
    )

    socket_listener: SocketListener = field(
        init=False,
        repr=False,
        hash=False,
        compare=False,
    )

    refresh_task: asyncio.Task = field(
        init=False,
        repr=False,
        hash=False,
        compare=False,
    )

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(base_url=self.gateau_api_url)

        async with self.session.get(
            f"/game/{self.room_code}/ramSubscriptions",
            headers=self.auth_header,
        ) as r:
            r.raise_for_status()
            subs = await r.json()
        addrs = [int(addr) for addr in subs["ramAddresses"]]

        logger.debug(addrs)
        logger.info(f"Listening to {len(addrs)} addresses.")

        monitor = RamMonitor(
            subscription=addrs,
            on_ram_change=self.handle_change,
        )

        self.socket_listener = await SocketListener(
            on_ram_frame=monitor.ram_frame_handler
        ).__aenter__()

        loop = asyncio.get_event_loop()
        self.refresh_task = loop.create_task(self.keep_token_fresh())

        return self

    async def __aexit__(self, *err):
        self.refresh_task.cancel()
        self.refresh_task = None

        await self.session.close()
        self.session = None

        await self.socket_listener.__aexit__(*err)
        self.socket_listener = None

    @property
    def auth_header(self):
        return {"Authorization": f"Bearer {self.id_token}"}

    async def handle_change(self, info: RamChangeInfo):
        logger.info(info)
        async with self.session.post(
            f"/game/{self.room_code}/ramChange",
            headers=self.auth_header,
            json=info.dict(),
        ) as r:
            r.raise_for_status()
        await asyncio.sleep(0)

    async def keep_token_fresh(self):
        """
        Periodically refresh the ID token used for requests
        """
        while True:
            await asyncio.sleep(CLIENT_REFRESH_INTERVAL_SECONDS)
            logger.info("Refreshing Token")
            async with AuthClient(api_key=self.gateau_auth_api_key) as auth_client:
                user = await auth_client.refresh(self.refresh_token)

                self.id_token = user.id_token
                self.refresh_token = user.refresh_token

    @classmethod
    async def from_email_and_password(
        cls: Type[GateauClient],
        email: str,
        password: str,
        room_code: str,
        gateau_api_url: str,
        gateau_auth_api_key: str,
    ):
        """
        Sign in with email and password
        """
        async with AuthClient(api_key=gateau_auth_api_key) as auth_client:
            user = await auth_client.sign_in_with_password(
                email=email,
                password=password,
            )
        return cls(
            room_code=room_code,
            id_token=user.id_token,
            refresh_token=user.refresh_token,
            gateau_api_url=gateau_api_url,
            gateau_auth_api_key=gateau_auth_api_key,
        )
