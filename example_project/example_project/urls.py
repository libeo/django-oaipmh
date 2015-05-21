from django.conf.urls import patterns, include, url
from django.contrib import admin
from .views import ExampleOAIProvider


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^oai/', ExampleOAIProvider.as_view()),
)
