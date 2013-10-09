"""Utilities for project Splango.

"""


def replace_insensitive(string, target, replacement):
    """Similar to string.replace() but is case insensitive

    Code borrowed from ``debug_toolbar`` and
    http://forums.devshed.com/python-programming-11/case-insensitive-string-replace-490921.html

    """
    no_case = string.lower()
    index = no_case.rfind(target.lower())
    if index >= 0:
        return string[:index] + replacement + string[index + len(target):]
    else:  # no results so return the original string
        return string


def is_first_visit(request):
    """Tell whether it is the first visit by ``request``'s visitor.

    Current algorithm is very basic. It performs the following nested checks:

    * if ``user`` in ``request`` is authenticated
    * if there is a HTTP_REFERER
    * if ``request``'s host matches the referer

    :param request: HTTP request
    :type request: :class:`django.http.HttpRequest`
    :return: True if this ``request`` is the first one by ``request``'s visitor
    :rtype: bool

    """
    if request.user.is_authenticated():
        return False

    referer = request.META.get("HTTP_REFERER", "").lower()

    if not referer:  # if no referer, then musta just typed it in
        return True

    if referer.startswith("http://"):
        referer = referer[7:]
    elif referer.startswith("https://"):
        referer = referer[8:]

    return not(referer.startswith(request.get_host()))


def user_model():
    # Safe User import for Django < 1.5
    try:
        from django.contrib.auth import get_user_model
    except ImportError:
        from django.contrib.auth.models import User
        return User
    else:
        return get_user_model()
