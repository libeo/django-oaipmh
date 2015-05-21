# coding: utf-8

from __future__ import unicode_literals
from datetime import datetime
from django.contrib.flatpages.models import FlatPage
from django_oaipmh import OAIProvider


class ExampleOAIProvider(OAIProvider):
    def items(self):
        return FlatPage.objects.all()

    def last_modified(self, obj):
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    def sets(self, obj):
        return []
