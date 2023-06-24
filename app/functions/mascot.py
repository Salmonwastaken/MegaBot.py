import logging
import dropbox
import discord
import os
import io
import aiohttp

logger = logging.getLogger("discord")


class poster:
    def __init__(self, client):
        logger.debug("Succesfully initialized mascotPoster")
        self.mascotChannel = client.get_channel(int(os.environ['mascotchannelId']))
        self.dan = client.get_user(int(os.environ['danId']))
        self.dbx = dropbox.Dropbox(oauth2_refresh_token=os.environ['dropboxRefresh'],
                            app_key=os.environ['dropboxClientId'],
                            app_secret=os.environ['dropboxClientSecret'])

    async def post(self):
        try:
            fileName, filePath, fileUrl = await self._getFileUrl()
        except TypeError:
            print("We failed to retrieve a file. No Mascot for thee")

        await self._postMascot(fileUrl, fileName)
        await self._deleteImage(filePath)

    async def _postMascot(self, fileUrl, fileName):
        async with aiohttp.ClientSession() as session:
            async with session.get(fileUrl) as resp:
                data = io.BytesIO(await resp.read())

                await self.mascotChannel.send(
                    file=discord.File(data, filename=fileName)
                )

    async def _getFileUrl(self):
        try:
            fileList = self.dbx.files_list_folder(path=os.environ['dropboxFolder'])

            fileName = fileList.entries[0].name
            filePath = fileList.entries[0].path_lower

            logger.debug(f"Found {fileName} at {filePath}")

            fileLink = self.dbx.files_get_temporary_link(path=filePath)

            return fileName, filePath, fileLink.link
        except:
            await self.mascotChannel.send(content=f"{self.dan} Man what the fuck there are no images left.")

    async def _deleteImage(self, filePath):
        self.dbx.files_delete_v2(path=filePath)