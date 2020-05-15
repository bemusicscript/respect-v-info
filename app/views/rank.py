import os
import json

from django.http import HttpResponse
from django.shortcuts import render
from django.urls import Resolver404
from django.conf import settings

from core.modules import elasticsearch
from app.api.user import InternalUserAPI


class Rank:
    def __init__(self):
        self.user_api = InternalUserAPI()
        self.es = elasticsearch.Connector(index="respect-v-leaderboard")
        self.prev_es = elasticsearch.Connector(index="respect-v-leaderboard-prev")
        self.user_es = elasticsearch.Connector(index="respect-v-users")

    def _get_archived_rank(self):
        pass

    def _get_user_data(self, steam_id64, filter_keys):
        _, user = self.user_es.get(
            {
                "from": 0,
                "size": 1,
                "query": {"match": {"id": steam_id64},},
                "_source": filter_keys,
            }
        )
        return user[0]["_source"]

    def _get_live_rank_preview(self):
        preview_data = {}
        user_keys = ["country_code", "avatar_url"]
        learderboard_keys = [
            "name",
            "id",
            "rank",
            "flu_rank",
            "major_tier",
            "game_count",
            "game_wins",
            "lp",
        ]
        for button in [4, 5, 6, 8]:
            button_data = []
            query = {
                "from": 0,
                "size": 10,
                "query": {"bool": {"must": [{"match": {"button": button}},]}},
                "sort": [{"rank": "asc"}],
            }
            _, data = self.es.get(query=query)
            for x in data:
                src = x["_source"]
                _preview = {
                    "abs_flu_rank": abs(src["flu_rank"] * -1)
                    if src["flu_rank"]
                    else None
                }
                user = self._get_user_data(steam_id64=src["id"], filter_keys=user_keys)
                _preview.update(
                    {"win_rate": "%.02f" % (src["game_wins"] / src["game_count"] * 100)}
                )
                [_preview.update({lk: src[lk]}) for lk in learderboard_keys]
                [_preview.update({uk: user[uk]}) for uk in user_keys]
                button_data.append(_preview)
            preview_data.update({str(button): button_data})
        return preview_data

    def _get_tier_name(self, major, minor):
        minor_val = ["", "I", "II", "III", "IV"]
        if major == 8:
            return "GRAND MASTER"
        elif major == 7:
            return "MASTER"
        elif major == 6:
            return "DIAMOND %s" % minor_val[minor]
        elif major == 5:
            return "PLATINUM %s" % minor_val[minor]
        elif major == 4:
            return "GOLD %s" % minor_val[minor]
        elif major == 3:
            return "SILVER %s" % minor_val[minor]
        elif major == 2:
            return "BRONZE %s" % minor_val[minor]
        else:
            return "IRON %s" % minor_val[minor]

    def _get_pp_rate(self, pp, fc):
        try:
            return "%.02f" % (pp / (fc + pp) * 100)
        except:
            # Should not reach here
            return 0.0

    def _get_win_rate(self, games, wins):
        try:
            return "%.02f" % (wins / games * 100)
        except:
            return 0.0

    def _get_live_details(self, button):
        query = {
            "from": 0,
            "size": 100,
            "query": {"bool": {"must": [{"match": {"button": button}},]}},
            "sort": [{"rank": "asc"}],
        }
        _, data = self.es.get(query=query)
        details = []
        _keys = list(data[0]["_source"].keys())
        _user_keys = ["country_code", "avatar_url"]
        _rank_keys = [
            "id",
            "rank",
            "flu_rank",
            "name",
            "major_tier",
            "lp",
            "maxcombo",
            "perfect",
            "game_count",
            "game_wins",
            "accuracy",
        ]
        for x in data:
            src = x["_source"]
            _details = {
                "tier_name": self._get_tier_name(src["major_tier"], src["minor_tier"]),
                "promote": True if src["minor_tier"] == 0 else False,
                "win_rate": self._get_win_rate(src["game_count"], src["game_wins"]),
                "pp_rate": self._get_pp_rate(src["perfect"], src["maxcombo"]),
                "game_loose": src["game_count"] - src["game_wins"],
                "abs_flu_rank": abs(src["flu_rank"] * -1) if src["flu_rank"] else None,
            }

            user = self._get_user_data(steam_id64=src["id"], filter_keys=_user_keys)
            [_details.update({k: user[k]}) for k in _user_keys]
            [_details.update({k: src[k]}) for k in _rank_keys]
            details.append(_details)
        return details

    def season_view(self, request, season):
        if season == "beta":
            raise Resolver404
        elif season == "pre":
            preview_data = self._get_live_rank_preview()
        else:
            raise Resolver404

        return render(
            request, "rank/season.html", {"season": season, "preview": preview_data}
        )

    def detail_view(self, request, season, button):
        if season == "beta":
            raise Resolver404
        elif season == "pre":
            detail_data = self._get_live_details(button)
        else:
            raise Resolver404

        return render(
            request,
            "rank/detail.html",
            {"season": season, "button": button, "detail": detail_data},
        )
