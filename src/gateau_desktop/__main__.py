import asyncio

import click

from gateau_desktop.gateau_client import GateauClient


async def run_server(
    email: str,
    password: str,
    room_code: str,
    gateau_api_url: str,
    gateau_auth_api_key: str,
):
    client = await GateauClient.from_email_and_password(
        email=email,
        password=password,
        room_code=room_code,
        gateau_api_url=gateau_api_url,
        gateau_auth_api_key=gateau_auth_api_key,
    )
    async with client:
        while True:
            await asyncio.sleep(0)


@click.command()
@click.option("--email", required=True, type=str)
@click.option("--password", required=True, type=str)
@click.option("--room", required=True, type=str)
@click.option("--api", required=True, type=str)
@click.option("--key", required=True, type=str)
def app(email: str, password: str, room: str, api: str, key: str):
    loop = asyncio.get_event_loop()
    loop.create_task(
        run_server(
            email=email,
            password=password,
            room_code=room,
            gateau_api_url=api,
            gateau_auth_api_key=key,
        )
    )
    loop.run_forever()


if __name__ == "__main__":
    app()
