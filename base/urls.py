from django.views.generic import TemplateView
from django.conf.urls import url
from django.urls import path

from app.views import Index, Song, User, Rank
from app.api import UserAPI, UpdateAPI

urlpatterns = [
    path("", Index.index, name="index"),
    path("thanks", Index.thanks, name="thanks"),
    path("qna", Index.qna, name="qna"),
    path("statistics", Index.statistics, name="statistics"),
    path("song", Song().index, name="song"),
    path("song/<int:song_id>", Song().info, name="song_info"),
    path("user", User().index, name="user"),
    path("user/<int:user_id>", User().info, name="user_info"),
    path("rank/ladder/<str:season>", Rank().season_view, name="rank"),
    path("rank/ladder/<str:season>/<int:button>", Rank().detail_view, name="rank"),
]

# API URL LIST
urlpatterns += [
    path(
        "api/user/history/<int:user_id>/<int:button>",
        UserAPI().history,
        name="api_user_history",
    ),
    path("api/user/search", UserAPI().search_id, name="api_user_search"),
    path("api/user/update", UpdateAPI().update, name="api_user_update"),
]

urlpatterns += [
    url(
        r"^robots.txt$",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
]
