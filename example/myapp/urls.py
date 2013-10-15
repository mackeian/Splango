from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r'^$', 'myapp.views.index', name='myapp_index'),
    url(r'^sample/$', 'myapp.views.sample', name='myapp_sample'),
    url(r'^goalie/(?P<goal_number>\d+)$', 'myapp.views.goalie', name="myapp_goalie"),
)
