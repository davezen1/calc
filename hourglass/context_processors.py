from django.conf import settings


def api_host(request):
    '''Include API_HOST in all request contexts'''
    return {'API_HOST': settings.API_HOST}


def show_debug_ui(request):
    '''Include show_debug_ui in all request contexts'''
    return {'show_debug_ui': settings.DEBUG and not settings.HIDE_DEBUG_UI}
