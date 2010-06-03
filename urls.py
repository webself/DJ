from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url( r'^$', 'dj.views.dj', name='dj' ),
    url( r'^save$', 'dj.views.save', name='djsave' ),
) 