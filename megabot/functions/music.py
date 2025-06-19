import os
import logging
import re
import spotipy
import yt_dlp
import lxml.html
from pprint import pformat


from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import quote_plus
from aiohttp import ClientSession

logger = logging.getLogger("discord")


# https://github.com/spotipy-dev/spotipy/issues/555#issuecomment-675099233
# For zero interaction token management
class CustomAuthManager:
    def __init__(self, clientId, clientSecret, refreshToken):
        self.auth = SpotifyOAuth(
            client_id=clientId,
            client_secret=clientSecret,
            redirect_uri="https://example.com/callback",
        )
        self.refresh_token = refreshToken
        self.current_token = None

    def get_access_token(self):
        import datetime

        now = datetime.datetime.now()

        # if no token or token about to expire soon
        if (
            not self.current_token
            or self.current_token["expires_at"] > now.timestamp() + 60
        ):
            self.current_token = self.auth.refresh_access_token(self.refresh_token)

        return self.current_token["access_token"]


class musicHandler:
    def __init__(self, message):
        logger.debug("Succesfully initialized musicHandler")
        self.musicChannel = os.environ["musicChannel"]
        self.steamedcatsID = os.environ["steamedcatsID"]
        self.msg = message
        self.sp = spotipy.Spotify(
            auth_manager=CustomAuthManager(
                clientId=os.environ["spotifyID"],
                clientSecret=os.environ["spotifySecret"],
                refreshToken=os.environ["spotifyRefresh"],
            )
        )

    async def onMessage(self):
        logger.debug("Message detected")
        type = await self._determineUriType()
        if type is None:
            return
        uri = await self._parseUri(type=type)
        if uri is None:
            await self.msg.reply("Couldn't find a song, sorry!")
            return
        await self._addToPlaylist(uri)
        await self._addReaction(uri)

    async def _determineUriType(self):
        logger.debug("Determining Uri type")
        if "open.spotify.com/track" in self.msg.content:
            return "spotify"
        if "spotify.link/" in self.msg.content:
            return "spoofy"
        if "youtube.com/watch" in self.msg.content:
            return "youtube"
        if "youtu.be" in self.msg.content:
            return "youtu.be"
        if "bandcamp.com/track/" in self.msg.content:
            return "bandcamp"
        else:
            logger.debug("Message doesn't contain anything we care about.")
            return None
        # TODO: add soundcloud etc

    async def _parseUri(self, type):
        logger.debug("Parsing uri")
        match type:
            case "spotify":
                regex = r"(?<=track/)[^?\n]+"
                uriID = re.search(regex, self.msg.content).group()
                return uriID
            # Spotify shortlinks :/
            # We get the URL shortened page, retrieve the actual Spotify link
            # and then parse that
            case "spoofy":
                regex = r"(?P<url>https?://[^\s]+)"
                uri = re.search(regex, self.msg.content).group()
                parse = await self._parsePage(uri)
                spotify_uri = parse.xpath("//link[@rel='canonical']")[0].get("href")
                regex = "(?<=track\/)[^?\n]+"
                uriID = re.search(regex, spotify_uri).group()
                return uriID
            case "bandcamp":
                regex = r"(?P<url>https?://[^\s]+)"
                uri = re.search(regex, self.msg.content).group()
                parse = await self._parsePage(uri)
                title = parse.find(".//title").text
                trackInfo = title.split("|")
                trackInfo.reverse()
                uriID = await self._searchSpotify(trackInfo)
                return uriID
            case "soundcloud":
                # TODO
                return
            case "youtube":
                regex = r"(?<=v\=)[^&\n]+"
                uri = re.search(regex, self.msg.content).group()
                trackInfo = await self._parseYoutube(uri)
                if trackInfo is None:
                    return None
                uriID = await self._searchSpotify(trackInfo)
                return uriID
            case "youtu.be":
                regex = r"(?<=be\/)[^?\n]+"
                uri = re.search(regex, self.msg.content).group()
                trackInfo = await self._parseYoutube(uri)
                if trackInfo is None:
                    return None
                uriID = await self._searchSpotify(trackInfo)
                return uriID
            # Catch all Case
            case _:
                logging.error("Unknown type")

    async def _parsePage(self, uri):
        async with ClientSession() as session:
            async with session.get(uri) as r:
                buf = await r.text()
                tree = lxml.html.fromstring(buf)
        return tree

    async def _guess_track_info(self, trackTitle):
        trackTitle = re.sub(r"[–—−]", "-", trackTitle)
        trackTitle = re.sub(r"[\[\(].*?[\]\)]", "", trackTitle).strip()

        #  Artist - Track
        match = re.match(r"^(.+?)\s*-\s*(.+)$", trackTitle)
        if match:
            artist = match.group(1).strip()
            track = match.group(2).strip()
            return artist, track

        # Pattern 2: <track> by <artist>
        match = re.match(r"^(.+?)\s+by\s+(.+)$", trackTitle)
        if match:
            track = match.group(1).strip()
            artist = match.group(2).strip()
            return artist, track

        # Pattern 3: <artist> | <track
        match = re.match(r"^(.+?)\s+\|\s+(.+)$", trackTitle)
        if match:
            track = match.group(1).strip()
            artist = match.group(2).strip()
            return artist, track

        return None

    async def _parseYoutube(self, uri):
        base_uri = "https://www.youtube.com/watch?v="
        full_url = "".join((base_uri, uri))

        details = yt_dlp.YoutubeDL(
            {
                "quiet": True,
                "skip_download": True,
                "extract_flat": "in_playlist",
                "no_warnings": True,
            }
        ).extract_info(url=full_url, download=False)

        logger.debug(details)

        if "track" in details:
            trackInfo = (details["artist"], details["track"])
        else:
            trackInfo = await self._guess_track_info(
                details["fulltitle"].lower().strip()
            )

        logger.debug(trackInfo)
        return trackInfo

    async def _searchSpotify(self, trackInfo):
        artistName, songName = trackInfo

        result = self.sp.search(
            q=f"remaster%20track:{songName}%20artist:{artistName}",
            market="GB",
            limit=5,
        )

        logger.debug(f"Looking up {songName} by {artistName}")

        for track in result["tracks"]["items"]:
            logger.debug(pformat(track))

            if track["name"].strip().lower() != songName.strip().lower():
                continue

            logger.debug(track["name"].strip().lower())

            artist_names = [
                artist["name"].strip().lower() for artist in track["artists"]
            ]

            if artistName.strip().lower() in artist_names:
                return track["uri"]

        return None

    async def _addToPlaylist(self, uri):
        logger.debug("Adding to playlist")
        self.sp.playlist_remove_all_occurrences_of_items(
            playlist_id=self.steamedcatsID, items=[uri]
        )
        self.sp.playlist_add_items(playlist_id=self.steamedcatsID, items=[uri])

    async def _addReaction(self, uri):
        await self.msg.add_reaction("👀")

    async def _getArtistGenre(self, uri):
        trackInfo = self.sp.track(track_id=uri)
        artistId = trackInfo["artists"][0]["id"]
        artistInfo = self.sp.artist(artist_id=artistId)
        return quote_plus(artistInfo["genres"][0])
