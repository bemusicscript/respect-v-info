import os
import json
import datetime

from django.conf import settings
from django.shortcuts import render
from django.urls import Resolver404
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


from core.modules import elasticsearch
from core.config import STEAMID64


class Statistics:
    def __init__(self):
        self.users = elasticsearch.Connector(index="users")
        self.matches = elasticsearch.Connector(index="matches")
        self.links, self.nodes = [], []

    def get_user_tier(self, user_id, button):
        query = {
            "_source": [button + ".major_tier"],
            "query": {"match": {"id": user_id}},
        }
        _, data = self.users.get(query=query)
        try:
            return data[0]["_source"][button]["major_tier"]
        except:
            return 0

    def get_matches(self, button):
        q = {"from": 0, "size": 10, "query": {"match": {"button": button}}}
        users = []
        match_data = self.matches.scan(query=q)
        for mat in match_data:
            m = mat["_source"]
            user_id, user_name = m["user_id"] - STEAMID64, m["user_name"]
            opnt_id, opnt_name = m["opponent_id"] - STEAMID64, m["opponent_name"]
            if m["opponent_id"] == 0:
                continue

            if user_id not in users:
                user_tier = self.get_user_tier(m["user_id"], button)
                self.nodes.append({"id": user_id, "group": user_tier})
                users.append(user_id)

            if opnt_id not in users:
                user_tier = self.get_user_tier(m["opponent_id"], button)
                self.nodes.append({"id": opnt_id, "group": user_tier})
                users.append(opnt_id)

            self.links.append({"source": user_id, "target": opnt_id, "value": 1})

        insert_queue = []
        for lnk in self.links:
            try:
                if lnk["source"] not in insert_queue and lnk["source"] not in users:
                    self.nodes["id"][lnk["source"]]
                    insert_queue.append(lnk["source"])
            except:
                self.nodes.append({"id": lnk["source"], "group": 0})
            try:
                self.nodes["id"][lnk["target"]]
            except:
                if lnk["target"] not in insert_queue and lnk["source"] not in users:
                    self.nodes.append({"id": lnk["target"], "group": 0})
                    insert_queue.append(lnk["target"])

        dataset = {"nodes": self.nodes, "links": self.links}
        with open("result.json", "w") as f:
            f.write(json.dumps(dataset, indent=4, sort_keys=True))
