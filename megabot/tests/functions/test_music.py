import pytest
import pytest_asyncio
import os
import discord

from megabot.functions.music import musicHandler


@pytest.fixture(autouse=True)
def change_env():
    os.environ["musicChannel"] = "1234"
    os.environ["steamedcatsID"] = "4321"
    os.environ["spotifyID"] = "5678"
    os.environ["spotifySecret"] = "hinekora!"
    os.environ["spotifyRefresh"] = "oriath!"
    os.environ["tenorKey"] = "the_atlas"


class TestmusicHandler(object):
    def test_init(self):
        MH = musicHandler(message="bye")

        assert MH.musicChannel == "1234"
        assert MH.steamedcatsID == "4321"
        assert MH.msg == "bye"

    @pytest.mark.asyncio
    async def test_onMessage(self, mocker):
        mocker.patch("megabot.functions.music.musicHandler._determineUriType")
        mocker.patch("megabot.functions.music.musicHandler._parseUri")
        mocker.patch("megabot.functions.music.musicHandler._addToPlaylist")
        mocker.patch("megabot.functions.music.musicHandler._addReaction")
        mocker.patch("discord.Message.reply")

        MH = musicHandler(message=discord.Message)
        await MH.onMessage()

        musicHandler._determineUriType.assert_called()
        musicHandler._parseUri.assert_called()
        musicHandler._addToPlaylist.assert_called()
        musicHandler._addReaction.assert_called()
