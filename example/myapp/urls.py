from django.conf.urls import patterns, include, url

urlpatterns = patterns(
    '',
    url(r'^sample/$', 'myapp.views.sample', name='myapp_sample'),
    url(r'^goalie/$', 'myapp.views.goalie', name="myapp_goalie"),
)
