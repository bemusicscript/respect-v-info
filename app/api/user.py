import os
import json
import datetime

from django.conf import settings
from django.shortcuts import render
from django.urls import Resolver404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from app.modules import steam
from core.modules import elasticsearch


class InternalUserAPI:
    def __init__(self):
        self.keys = [4, 5, 6, 8]
        self.steam = steam.Steam()
        self.es_matches = elasticsearch.Connector(index="respect-v-matches")
        self.es_users = elasticsearch.Connector(index="respect-v-users")
        self.es_rank = elasticsearch.Connector(index="respect-v-leaderboard")
        self.es_prev_rank = elasticsearch.Connector(index="respect-v-leaderboard-prev")


class UserAPI:
    def __init__(self):
        self.steam = steam.Steam()
        self.es_user_button = elasticsearch.Connector(index="respect-v-btn-user-count")
        self.es_matches = elasticsearch.Connector(index="respect-v-matches")
        self.es_users = elasticsearch.Connector(index="respect-v-users")

    def _get_user_info(self, user_id, button):
        query = {
            "query": {
                "bool": {
                    "must": [{"match": {"id": user_id}}, {"match": {"button": button}},]
                }
            }
        }
        _, src = self.es_users.get(query=query)
        try:
            return src[0]["_source"]
        except:
            return None

    def _set_match_result(self, src):
        round = len(src["match"]["song"]) + (1 if src["hard_match"] else 0)
        self.round_count += round

        user_score = sum(src["match"]["user_score"])
        opp_score = sum(src["match"]["opponent_score"])

        normal_wl = self.statistics["round"]["normal"]["wl"]
        if user_score > opp_score:
            normal_wl["win"] += 1
        elif user_score == opp_score:
            normal_wl["draw"] += 1
        else:
            normal_wl["lose"] += 1

        if src["hard_match"]:
            hard_wl = self.statistics["round"]["hard"]["wl"]
            if src["hard_match"]["user_score"] > src["hard_match"]["opponent_score"]:
                hard_wl["win"] += 1
            else:
                hard_wl["lose"] += 1
            if src["hard_match"]["user_accuracy"] != 0:
                self.hard_acc.append(src["hard_match"]["user_accuracy"])

        for acc in src["match"]["user_accuracy"]:
            if acc != 0:
                self.accuracy.append(acc)

    def _get_statistics(self, user_id, button):
        self.round_count = 0
        self.accuracy, self.hard_acc = [], []
        self.match_players = {}
        self.user = self._get_user_info(user_id, button)
        if not self.user:
            return False

        self.statistics = {
            "total": {
                "pfn": None,
                "win": self.user["win_count"],
                "lose": self.user["game_count"] - self.user["win_count"],
            },
            "round": {
                "normal": {
                    "wl": {"win": 0, "draw": 0, "lose": 0},
                    "acc": {"avg": 0.0, "max": 0.0},
                },
                "hard": {"wl": {"win": 0, "lose": 0}, "acc": {"avg": 0.0, "max": 0.0},},
            },
            "user": {},
        }

        query = {
            "from": 0,
            "size": 1000,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"user_id": user_id}},
                        {"match": {"button": button}},
                    ],
                }
            },
            "sort": [{"datetime": "desc"}],
        }
        hits, result = self.es_matches.get(query=query)
        for x in result:
            src = x["_source"]
            self._set_match_result(src)
            if not src["opponent_id"] in self.match_players.keys():
                self.match_players.update({src["opponent_id"]: 1})
            else:
                self.match_players[src["opponent_id"]] += 1

        self.statistics["total"]["pfn"] = {
            "perfect": self.user["pp_count"],
            "maxcombo": self.user["mc_count"],
            "normal": self.round_count - self.user["pp_count"] - self.user["mc_count"],
        }

        normal_acc = self.statistics["round"]["normal"]["acc"]
        try:
            normal_acc["max"] = max(self.accuracy)
            normal_acc["avg"] = sum(self.accuracy) / len(self.accuracy)
        except:
            normal_acc["max"], normal_acc["avg"] = 0, 0

        hard_acc = self.statistics["round"]["hard"]["acc"]
        try:
            hard_acc["max"] = max(self.hard_acc)
            hard_acc["avg"] = sum(self.hard_acc) / len(self.hard_acc)
        except:
            hard_acc["max"], hard_acc["avg"] = 0, 0

        return True

    def history(self, request, user_id, button):
        try:
            _from = request.GET["from"]
        except:
            _from = 0
        query = {
            "from": _from,
            "size": 50,
            "query": {
                "bool": {
                    "must": [
                        {"match": {"user_id": user_id}},
                        {"match": {"button": button}},
                    ]
                }
            },
            "sort": [{"datetime": "desc"}],
        }
        hits, result = self.es_matches.get(query=query)
        stat_result = self._get_statistics(user_id, button)
        if not stat_result:
            return JsonResponse(
                {"rank": None, "statistics": None, "history": result}, safe=False
            )
        _, data = self.es_user_button.get(
            query={"query": {"match": {"button": button}}}
        )
        _, user = self.es_users.get(
            query={
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"id": user_id}},
                            {"match": {"button": button}},
                        ]
                    }
                },
                "_source": ["rank"],
            }
        )
        rank_status = {
            "user_rank": user[0]["_source"]["rank"],
            "user_count": data[0]["_source"]["count"],
        }
        return JsonResponse(
            {"rank": rank_status, "statistics": self.statistics, "history": result},
            safe=False,
        )

    @csrf_exempt
    def search_id(self, request):
        try:
            vanity_name = request.POST.get("steam_id")
            if len(vanity_name) == 17 and vanity_name.isdigit():
                user_id = vanity_name
            else:
                user_id = self.steam.get_user_id(vanity_name)
            if user_id:
                value = self.steam.get_user_summary(user_id)
            else:
                value = None
        except:
            value = None
        return JsonResponse({"result": value}, safe=False)
