import logging
import discord
import os
from aiohttp import ClientSession
from io import BytesIO

logger = logging.getLogger("discord")


class poster:
    def __init__(self, client):
        logger.debug("Succesfully initialized mascotPoster")
        self.mascotChannel = client.get_channel(int(os.environ['mascotchannelId']))

    async def post(self):
        await self._postMascot()

    async def _postMascot(self):
        async with ClientSession() as session:
            async with session.get("https://cataas.com/cat") as resp:
                if resp.status != 200:
                    return await self.mascotChannel.send("cataas.com failed to return a cat! D:")
                data = BytesIO(await resp.read())

                await self.mascotChannel.send(
                    file=discord.File(data, filename="cat.jpeg")
                )
