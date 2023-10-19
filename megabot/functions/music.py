import os
import logging
import re
import spotipy
import requests
import json
import yt_dlp

from random import randrange
from spotipy.oauth2 import SpotifyOAuth
from urllib.parse import quote_plus, quote
from bs4 import BeautifulSoup

logger = logging.getLogger("discord")


# https://github.com/spotipy-dev/spotipy/issues/555#issuecomment-675099233
# For zero interaction token management
class CustomAuthManager:
    def __init__(self, clientId, clientSecret, refreshToken):
        self.auth = SpotifyOAuth(client_id=clientId, client_secret=clientSecret, redirect_uri="https://example.com/callback")
        self.refresh_token = refreshToken
        self.current_token = None

    def get_access_token(self):
        import datetime
        now = datetime.datetime.now()
		
		# if no token or token about to expire soon
        if not self.current_token or self.current_token["expires_at"] > now.timestamp() + 60:
            self.current_token = self.auth.refresh_access_token(self.refresh_token)

        return self.current_token["access_token"]

class musicHandler():
    def __init__(self, message):
            logger.debug("Succesfully initialized musicHandler")
            self.musicChannel = os.environ["musicChannel"]
            self.steamedcatsID = os.environ["steamedcatsID"]
            self.msg = message
            self.sp = spotipy.Spotify(auth_manager=CustomAuthManager(clientId=os.environ["spotifyID"],
                                    clientSecret=os.environ["spotifySecret"],
                                    refreshToken=os.environ["spotifyRefresh"]))
    
    async def onMessage(self):
        logger.debug("Message detected")
        type = await self._determineUriType()
        if type == None:
            return
        uri = await self._parseUri(type=type)
        if uri == None:
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
        # TODO: add bandcamp,soundcloud etc

    async def _parseUri(self, type):
        logger.debug("Parsing uri")
        match type:
            case "spotify":
                regex = "(?<=track\/)[^?\n]+"
                uriID = re.search(regex, self.msg.content).group()
                return uriID
            # Spotify shortlinks :/
            # We get the URL shortened page, retrieve the actual Spotify link and then parse that
            case "spoofy":
                regex = "(?P<url>https?://[^\s]+)"
                uri = re.search(regex, self.msg.content).group()
                soup = await self._soupifyPage(uri)
                spotify_uri = soup.find(rel="canonical")["href"]
                regex = "(?<=track\/)[^?\n]+"
                uriID = re.search(regex, spotify_uri).group()
                return uriID
            case "bandcamp":
                regex = "(?P<url>https?://[^\s]+)"
                uri = re.search(regex, self.msg.content).group()
                soup = await self._soupifyPage
                title = soup.head.title.get_text()
                trackInfo = title.split('|')
                uriID = await self._searchSpotify(trackInfo)
                return uriID
            case "soundcloud":
                # TODO
                return
            case "youtube":
                regex = "(?<=v\=)[^&\n]+"
                uri = re.search(regex, self.msg.content).group()
                trackInfo = await self._parseYoutube(uri)
                if trackInfo == None:
                    return None
                uriID = await self._searchSpotify(trackInfo)
                return uriID
            case "youtu.be":
                regex = "(?<=be\/)[^?\n]+"
                uri = re.search(regex, self.msg.content).group()
                trackInfo = await self._parseYoutube(uri)
                if trackInfo == None:
                    return None
                uriID = await self._searchSpotify(trackInfo)
                return uriID
            # Catch all Case
            case _:
                logging.error("Unknown type, we really shouldn't be hitting this. Ever")

    async def _soupifyPage(self, uri):
        response = requests.get(uri)
        soup = BeautifulSoup(response.content, features="lxml")
        return soup

    async def _parseYoutube(self, uri):
        base_uri = "https://www.youtube.com/watch?v="
        full_url = "".join((base_uri, uri))
        trackInfo = []
        details = yt_dlp.YoutubeDL({'quiet': 'True'}).extract_info(url=full_url, download=False)
        if 'track' in details:
            track, artist = details['track'], details['artist']
            trackInfo.append(track)
            trackInfo.append(artist)
            print(trackInfo)
            return trackInfo
        else:
            return None

    async def _searchSpotify(self, trackInfo):
        track = self.sp.search(q=f"remaster%20track:{trackInfo[0]}%20artist:{trackInfo[1]}",market='GB',limit=1)
        if (trackInfo[0].strip() in track['tracks']['items'][0]['name']) and (trackInfo[1].strip() in track['tracks']['items'][0]['artists'][0]['name']):
            return track['tracks']['items'][0]['uri']
        else:
            return None

    async def _addToPlaylist(self, uri):
        logger.debug("Adding to playlist")
        self.sp.playlist_remove_all_occurrences_of_items(playlist_id=self.steamedcatsID,items=[uri])
        self.sp.playlist_add_items(playlist_id=self.steamedcatsID,items=[uri])
        
    async def _addReaction(self, uri):
        chance = randrange(100)
        if chance > 99:
            gifUrl = await self._obtainGif(uri)
            if gifUrl == None:
                await self.msg.add_reaction("👀")
            else:
                await self.msg.reply(f"I looked up the genre of that song and found this gif! {gifUrl}")
        else:
            await self.msg.add_reaction("👀")

    async def _obtainGif(self, uri):
        apikey = os.environ["tenorKey"]
        ckey = "my_test_app"
        search_term = await self._getArtistGenre(uri)
        r = requests.get(
            f"https://tenor.googleapis.com/v2/search?q={search_term}&key={apikey}&client_key={ckey}&limit=1")
        if r.status_code == 200:
            gif = json.loads(r.content)
            return gif["results"][0]["url"]
        else:
            return None

    async def _getArtistGenre(self, uri):
        trackInfo = self.sp.track(track_id=uri)
        artistId = trackInfo["artists"][0]["id"]
        artistInfo = self.sp.artist(artist_id=artistId)
        return quote_plus(artistInfo["genres"][0])