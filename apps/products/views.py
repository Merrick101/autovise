from django.http import HttpResponse


def index(request):
    return HttpResponse("Products app is connected!")
