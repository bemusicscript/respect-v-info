import json
import os
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import Resolver404
from django.conf import settings

from app.modules.steam import Steam
from app.api.update import InternalUpdateAPI
from core.modules import elasticsearch


class User:
    def __init__(self):
        self.update_api = InternalUpdateAPI()
        self.es = elasticsearch.Connector(index="respect-v-users")
        self.update_user = elasticsearch.Connector(index="respect-v-user-update")

    def index(self, request):
        return render(request, "user/index.html")

    def info(self, request, user_id):
        query = {"query": {"match": {"id": user_id}}}
        hits, data = self.es.get(query=query)
        if not data:
            self.update_api.internal_user_update(user_id)
            hits, data = self.es.get(query=query)
        self.result = {4: None, 5: None, 6: None, 8: None}
        for key in self.result.keys():
            for val in data:
                if val["_source"]["button"] == key:
                    self.result.update({key: val["_source"]})
        if hits != 0:
            values = Steam().get_user_summary(user_id=user_id)
            steam_info = {
                "propic_url": values["avatarfull"],
                "name": values["personaname"],
                "profile_url": values["profileurl"],
            }
        else:
            steam_info = None
        _, _user = self.update_user.get(query={"query": {"match": {"id": user_id}}})
        if _user:
            update_result = _user[0]["_source"]
        else:
            update_result = {"last_updated_at": None, "result": False}

        return render(
            request,
            "user/info.html",
            {
                "id": user_id,
                "steam_info": steam_info,
                "info": self.result,
                "update": update_result,
            },
        )

    def history(self, request, user_id):
        query = {
            "from": 0,
            "size": 50,
            "query": {"bool": {"must": [{"match": {"user_id": user_id}},]}},
            "sort": [{"datetime": "desc"}],
        }
        hits, data = self.es.get(query=query)
        json_data = {"ladder_info": data}

        # 이건 나중에 user table에서 따로 조회하기
        json_data.update({"name": user_id})
        return render(request, "user/history.html", json_data)
