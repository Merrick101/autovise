from django.http import HttpResponse


def index(request):
    return HttpResponse("Pages app is connected!")
