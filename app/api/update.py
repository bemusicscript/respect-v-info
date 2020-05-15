import os
import json
import struct
import datetime

from django.shortcuts import render
from django.urls import Resolver404
from django.conf import settings
from django.http import HttpResponse, JsonResponse

from app.modules.steam import Steam
from core.config import API, DATA_PATH, STEAMID64
from core.modules import elasticsearch
from core.modules.userinfo import UserInfo
from core.modules.history import PlayHistory
from core.modules.respectv import Connector, Parser


class InternalUpdateAPI:
    def __init__(self):
        self.steam = Steam()
        self.user_es = elasticsearch.Connector(index="respect-v-users")
        self.match_es = elasticsearch.Connector(index="respect-v-matches")

    def _download_userinfo(self, steam_id64):
        _, path = self._get_user_connector("userinfo", steam_id64)
        return path

    def _download_history(self, steam_id64):
        _, path = self._get_user_connector("playhistory", steam_id64)
        return path

    def _get_steam_profile(self, steamid64):
        summary = self.steam.get_user_summary(steamid64)
        return {
            "steam_name": summary["personaname"],
            "avatar_url": summary["avatarfull"],
            "profile_url": summary["profileurl"],
            "country_code": summary["loccountrycode"]
            if "loccountrycode" in summary.keys()
            else "UNK",
        }

    def _get_last_match_datetime(self, steam_id64):
        query = {
            "from": 0,
            "size": 1,
            "_source": ["datetime"],
            "query": {"bool": {"must": [{"match": {"user_id": steam_id64}},]}},
            "sort": [{"datetime": "desc"}],
        }
        _, result = self.match_es.get(query=query)
        if not result:
            return None
        return datetime.datetime.strptime(
            result[0]["_source"]["datetime"], "%Y-%m-%dT%H:%M:%S"
        )

    def internal_user_update(self, steam_id64):
        """ Download Userdata """
        user_info, history_results = [], []
        userinfo_path = self._download_userinfo(steam_id64)
        history_path = self._download_history(steam_id64)
        _path = userinfo_path.split("/")[-1]
        steam_id3 = int(_path.split(".")[:-1][0])
        steam_profile = self._get_steam_profile(steam_id64)

        """ Update UserInfo """
        with open(userinfo_path, "rb") as f:
            data = f.read()
            ui = UserInfo(data=data, steam_id=steam_id3)
            for data in ui.parse():
                data.update(steam_profile)
                user_info.append(data)
        self.user_es.bulk_update(user_info, id_key="sign_val", upsert=True)

        """ Update History """
        last_matched_at = self._get_last_match_datetime(steam_id64=steam_id64)
        history_parser = Parser(path=history_path)
        for button in history_parser.buttons:
            for game_data in history_parser.get_userdata(button=button):
                _history = PlayHistory(game_data)
                result = _history.get_history_data()
                result = self._history_field_reassembly(button, result)
                if last_matched_at is None:
                    history_results.append(result)
                elif result["datetime"] > last_matched_at:
                    history_results.append(result)
        self.match_es.bulk_insert(history_results)

        """ Remove User File """
        os.remove(userinfo_path)
        os.remove(history_path)

    def update_userinfo(self):
        user_info = []
        path = self._download_userinfo(steam_id64)
        path = path.split("/")[-1]
        steam_id3 = int(path.split(".")[:-1][0])
        steam_profile = self._get_steam_profile(steam_id64)
        with open(DATA_PATH + "/USERINFO/" + path, "rb") as f:
            data = f.read()
            ui = UserInfo(data=data, steam_id=steam_id3)
            for data in ui.parse():
                data.update(steam_profile)
                user_info.append(data)
        self.user_es.bulk_update(user_info, id_key="sign_val", upsert=True)

    def _get_user_connector(self, api_name, steam_id64):
        base_path = "/".join(os.path.realpath(__file__).split("/")[:-3]) + "/core/temp"
        request_data = API[api_name]["request_data"]
        request_data += struct.pack("Q", steam_id64)
        conn = Connector(api_name, request_data=request_data)
        save_path = "%s/%d.%s" % (
            base_path,
            steam_id64 - STEAMID64,
            "userdata" if api_name == "userinfo" else "bin",
        )
        conn.save(path=save_path)
        return conn, save_path

    def _get_last_match_datetime(self, steam_id64):
        query = {
            "from": 0,
            "size": 1,
            "_source": ["datetime"],
            "query": {"bool": {"must": [{"match": {"user_id": steam_id64}},]}},
            "sort": [{"datetime": "desc"}],
        }
        _, result = self.match_es.get(query=query)
        if not result:
            return None
        return datetime.datetime.strptime(
            result[0]["_source"]["datetime"], "%Y-%m-%dT%H:%M:%S"
        )

    def _history_field_reassemble(self, button, data):
        matches = data["matches"]
        result = {
            "datetime": data["datetime"],
            "button": button,
            "user_id": data["player"]["a"]["id"],
            "user_name": data["player"]["a"]["name"],
            "opponent_id": data["player"]["b"]["id"],
            "opponent_name": data["player"]["b"]["name"],
            "gain_lp": data["gain_lp"],
            "match": None,
            "hard_match": None,
        }

        new_matches = {
            "song": [],
            "user_score": [],
            "opponent_score": [],
            "user_accuracy": [],
            "opponent_accuracy": [],
        }
        if len(matches) > 3:
            print(data)
        if len(matches) == 3:
            hard = matches.pop(3)
            result["hard_match"] = {
                "song": hard["song"],
                "user_score": hard["result"]["a"]["score"],
                "opponent_score": hard["result"]["b"]["score"],
                "user_accuracy": hard["result"]["a"]["accuracy"],
                "opponent_accuracy": hard["result"]["b"]["accuracy"],
            }

        for i in matches:
            new_matches["song"].append(matches[i]["song"])
            new_matches["user_score"].append(matches[i]["result"]["a"]["score"])
            new_matches["opponent_score"].append(matches[i]["result"]["b"]["score"])
            new_matches["user_accuracy"].append(matches[i]["result"]["a"]["accuracy"])
            new_matches["opponent_accuracy"].append(
                matches[i]["result"]["b"]["accuracy"]
            )

        result["match"] = new_matches
        sum_user_score = sum(new_matches["user_score"])
        sum_opponent_score = sum(new_matches["opponent_score"])
        if result["hard_match"]:
            result["win"] = (
                sum_user_score + result["hard_match"]["user_score"]
                > sum_opponent_score + result["hard_match"]["opponent_score"]
            )
        else:
            result["win"] = sum_user_score > sum_opponent_score
        return result


class UpdateAPI:
    def __init__(self):
        self.update_api = InternalUpdateAPI()
        self.user_update = elasticsearch.Connector(index="respect-v-user-update")

    def _update_done(self, steam_id64):
        return self.user_update.update(
            body={
                "updating": False,
                "id": steam_id64,
                "last_updated_at": datetime.datetime.now(),
            },
            id_key="id",
        )

    def _update_start(self, steam_id64):
        return self.user_update.update(
            body={"updating": True, "id": steam_id64}, id_key="id"
        )

    def check_request_limit(self, last_updated_at, limit_sec=600):
        """ limit_sec를 초과한 경우, True를 리턴하고 데이터를 갱신한다. """
        dt = datetime.datetime.strptime(last_updated_at, "%Y-%m-%dT%H:%M:%S.%f")
        if (datetime.datetime.now() - dt).total_seconds() > limit_sec:
            return True
        return False

    def _update_user_info(self, steam_id64):
        self.update_api.internal_user_update(steam_id64)
        self._update_done(steam_id64=steam_id64)
        return True, datetime.datetime.now()

    def _update(self, id64):
        _, data = self.user_update.get({"query": {"match": {"id": id64}}})
        if data:
            """ 업데이트를 1번 이상 진행한 유저 """
            _, user = self.user_update.get(query={"query": {"match": {"id": id64}}})
            user = user[0]["_source"]
            if self.check_request_limit(user["last_updated_at"]):
                """ 갱신 가능 """
                status, last_updated_at = self._update_user_info(steam_id64=id64)
            else:
                """ 갱신 제한 시간이 지나지 않음 """
                status, last_updated_at = False, user["last_updated_at"]
        else:
            """ 최초 업데이트. 무조건 업뎃 """
            body = {
                "id": id64,
                "updating": True,
                "last_updated_at": datetime.datetime.now(),
            }
            self.user_update.update(body=body, id_key="id", upsert=True)
            status, last_updated_at = self._update_user_info(steam_id64=id64)
            self.user_update.update(body={"updating": False, "id": id64}, id_key="id")
        return status, last_updated_at

    def update(self, request):
        referer = request.headers.get("Referer")
        id64 = int(referer.split("/")[-1])
        status, last_updated_at = self._update(id64=id64)
        return JsonResponse(
            {"status": status, "last_updated_at": last_updated_at}, safe=False
        )
