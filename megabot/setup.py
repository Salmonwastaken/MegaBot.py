from setuptools import setup
import megabot

setup(
    name="megabot",
    description="He megabotted all over those guys",
    version="0.10.1",
    author="Salmonwastaken",
    license="MIT",
    packages=["megabot"],
    include_package_data=True,
    install_requires=[
        "aiohttp==3.8.4",
        "aiosignal==1.3.1",
        "async-timeout==4.0.2",
        "attrs==23.1.0",
        "beautifulsoup4==4.12.2",
        "Brotli==1.1.0",
        "certifi==2022.12.7",
        "charset-normalizer==3.1.0",
        "cssselect==1.2.0",
        "discord.py==2.2.2",
        "dropbox==11.36.0",
        "requests==2.28.2",
        "six==1.16.0",
        "soupsieve==2.4.1",
        "spotipy==2.23.0",
        "stone==3.3.1",
        "urllib3==1.26.15",
        "websockets==11.0.3",
        "yarl==1.9.1",
        "yt-dlp==2023.10.13",
    ],
)
