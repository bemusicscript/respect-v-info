import json

import requests

from core.config import STEAM_PUB_API_KEY


class Steam:
    def __init__(self):
        self.key = STEAM_PUB_API_KEY

    def get_user_summary(self, user_id):
        url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}"
        result = requests.get(url=url.format(api_key=self.key, steam_id=user_id))
        return result.json()["response"]["players"][0]

    def get_user_id(self, vanity_name):
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v1/?key={api_key}&vanityurl={vanity_name}"
        result = requests.get(url=url.format(api_key=self.key, vanity_name=vanity_name))
        result = result.json()
        if result["response"]["success"] == 1:
            return result["response"]["steamid"]
        else:
            return None
