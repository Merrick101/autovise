from django.contrib.sitemaps import views as sitemaps_views


def sitemap_index_xml(request, *args, **kwargs):
    resp = sitemaps_views.index(request, *args, **kwargs)
    resp["Content-Type"] = "application/xml"
    return resp


def sitemap_section_xml(request, *args, **kwargs):
    resp = sitemaps_views.sitemap(request, *args, **kwargs)
    resp["Content-Type"] = "application/xml"
    return resp
