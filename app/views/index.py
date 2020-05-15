from django.shortcuts import render


class Index:
    def index(request):
        return render(request, "index.html")

    def qna(request):
        return render(request, "qna.html")

    def statistics(request):
        return render(request, "statistics.html")

    def thanks(request):
        return render(request, "thanks.html")
