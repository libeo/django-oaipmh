# coding: utf-8

from __future__ import unicode_literals
from datetime import datetime
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django_oaipmh import OAIProvider


class ExampleOAIProvider(OAIProvider):
    identify_config = {
        'name': 'oai test project',
        'earliest_date': '1990-02-01T12:00:00Z',
        'granularity': 'YYYY-MM-DDThh:mm:ssZ',
        'compression': 'deflate',
        'identifier_scheme': 'oai',
        'repository_identifier': 'test.localhost',
        'identifier_delimiter': ':',
        'sample_identifier': 'oai:lcoa1.loc.gov:loc.music/musdi.002'
    }

    def items(self):
        return FlatPage.objects.all()

    def item(self, item_identifier):
        # oai:example.com:page/2
        set_id = item_identifier.split(':')[2]
        # page/2
        item_id = set_id.split('/')[1]
        # 2
        return FlatPage.objects.get(pk=item_id)

    def last_modified(self, obj):
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    def oai_identifier(self, obj):
        # oai identifier for a given object
        return 'oai:%s:page/%s' % (Site.objects.get_current().domain, obj.pk)

    def record_identifier(self, obj):
        # oai identifier for a given object
        return 'http://%s:%s' % (Site.objects.get_current().domain, obj.pk)

    def sets(self, obj):
        return []

    def sets_list(self):
        return [
            {'spec': 'Video', 'name': 'Vidéo', 'description': 'Patate'},
            {'spec': 'Video2', 'name': 'Vidéo2', 'description': 'Patate2'}
        ]
