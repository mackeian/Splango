from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext


def index(request):
    return render_to_response("index.html", {}, RequestContext(request))


def sample(request):
    cities = [
        {'name': 'Mumbai', 'population': '19,000,000', 'country': 'India'},
        {'name': 'Calcutta', 'population': '15,000,000', 'country': 'India'},
        {'name': 'New York', 'population': '20,000,000', 'country': 'USA'},
        {'name': 'Chicago', 'population': '7,000,000', 'country': 'USA'},
        {'name': 'Tokyo', 'population': '33,000,000', 'country': 'Japan'},
    ]

    return render_to_response("sample.html", {"cities":cities}, RequestContext(request))


def goalie(request, goal_number):
    exp = request.experiments_manager
    exp.log_goal("features.goal_%s" % goal_number)
    return redirect(reverse('myapp_sample'))
