from django.http import HttpResponse


def index(request):
    return HttpResponse("Orders app is connected!")
