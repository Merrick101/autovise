from django.http import HttpResponse


def index(request):
    return HttpResponse("Assets app is connected!")
