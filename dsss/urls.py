from django.conf.urls.defaults import *

urlpatterns = patterns('dsss.views',
    url(r'^(?P<name>[-\w]+)\-(?P<year>\d{4})\-(?P<month>\d{1,2})\-(?P<day>\d{1,2}).css', 'get_stylesheet', name='seasonal-stylesheet'),
)
