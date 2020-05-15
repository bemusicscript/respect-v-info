from django.http import HttpResponse
from django.shortcuts import render
from django.urls import Resolver404
from django.conf import settings

from core.modules import elasticsearch


class Song:
    def __init__(self):
        self.es = elasticsearch.Connector(index="respect-v-songs")

    def index(self, request):
        query = {"size": 500, "query": {"match_all": {}}}
        hits, data = self.es.get(query=query)
        return render(request, "song/index.html", {"songs": data})

    def info(self, request, song_id):
        query = {"query": {"match": {"id": song_id}}}
        hits, data = self.es.get(query=query)
        if hits != 1:
            raise Resolver404
        return render(
            request, "song/info.html", {"id": song_id, "info": data[0]["_source"]}
        )
