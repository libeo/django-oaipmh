# file django_oaipmh/views.py
#
#   Copyright 2013 Emory University Libraries
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from django.conf import settings
from django.contrib.sites.models import Site
from django.views.generic import TemplateView


class OAIProvider(TemplateView):
    content_type = 'text/xml'  # possibly application/xml ?
    identify_config = {
        'name': 'oai repo name',
        'earliest_date': '1990-02-01T12:00:00Z',
        'granularity': 'YYYY-MM-DDThh:mm:ssZ',
        'compression': 'deflate',
        'identifier_scheme': 'oai',
        'repository_identifier': 'lcoa1.loc.gov',
        'identifier_delimiter': ':',
        'sample_identifier': 'oai:lcoa1.loc.gov:loc.music/musdi.002'
    }

    # modeling on sitemaps: these methods should be implemented
    # when extending OAIProvider

    def items(self):
        # list/generator/queryset of items to be made available via oai
        # NOTE: this will probably have other optional parameters,
        # e.g. filter by set or date modified
        # - could possibly include find by id for GetRecord here also...
        pass

    def item(self, item_identifier):
        # specific item for GetRecord verb.
        # item_identifier will be what is returned by oai_identifier()
        # for exemple 'oai:example.com:page/2'
        pass

    def last_modified(self, obj):
        # datetime object was last modified
        pass

    def sets_list(self):
        # list/generator/queryset of sets to be made available via oai
        return [
            {'spec': 'Example', 'name': 'Example', 'description': 'desc'},
        ]

    def oai_identifier(self, obj):
        # oai identifier for a given object
        return 'oai:%s:%s' % (Site.objects.get_current().domain,
                              obj.get_absolute_url())

    def record_identifier(self, obj):
        # oai identifier for a given object
        return 'http://%s:%s' % (Site.objects.get_current().domain,
                                 obj.get_absolute_url())

    def sets(self, obj):
        # list of set identifiers for a given object
        return []

    # TODO: get metadata record for a given object in a given metadata format

    def render_to_response(self, context, **response_kwargs):
        # all OAI responses should be xml
        if 'content_type' not in response_kwargs:
            response_kwargs['content_type'] = self.content_type

        # add common context data needed for all responses
        context.update({
            'verb': self.oai_verb,
            'url': self.request.build_absolute_uri(self.request.path),
        })
        return super(TemplateView, self) \
            .render_to_response(context, **response_kwargs)

    def identify(self):
        self.template_name = 'django_oaipmh/identify.xml'
        # TODO: these should probably be class variables/configurations
        # that extending classes could set
        identify_data = {
            'name': self.identify_config['name'],
            # perhaps an oai_admins method with default logic settings.admins?
            'admins': (email for name, email in settings.ADMINS),
            'earliest_date': self.identify_config['earliest_date'],   # placeholder
            # should probably be a class variable/configuration
            'deleted': 'no',  # no, transient, persistent (?)
            # class-level variable/configuration (may affect templates also)
            'granularity': self.identify_config['granularity'],  # or YYYY-MM-DD
            # class-level config?
            'compression': self.identify_config['compression'],  # gzip?  - optional
            # description - optional
            # (place-holder values from OAI docs example)
            'identifier_scheme': self.identify_config['identifier_scheme'],
            'repository_identifier': self.identify_config['repository_identifier'],
            'identifier_delimiter': self.identify_config['identifier_delimiter'],
            'sample_identifier': self.identify_config['sample_identifier']
        }
        return self.render_to_response(identify_data)

    def list_identifiers(self):
        self.template_name = 'django_oaipmh/list_identifiers.xml'
        items = []
        # TODO: eventually we will need pagination with oai resumption tokens
        # should be able to model similar to django.contrib.sitemap
        for i in self.items():
            item_info = {
                'identifier': self.oai_identifier(i),
                'last_modified': self.last_modified(i),
                'sets': self.sets(i)
            }
            items.append(item_info)
        return self.render_to_response({'items': items})

    def list_sets(self):
        self.template_name = 'django_oaipmh/list_sets.xml'
        return self.render_to_response({'sets': self.sets_list()})

    def list_metadata_formats(self):
        self.template_name = 'django_oaipmh/list_metadata_formats.xml'
        return self.render_to_response({})

    def list_records(self):
        self.template_name = 'django_oaipmh/list_records.xml'
        items = self.items()
        # TODO: eventually we will need pagination with oai resumption tokens
        # should be able to model similar to django.contrib.sitemap
        for i in items:
            i.identifier = self.oai_identifier(i)
            i.record_identifier = self.record_identifier(i)
            i.last_modified = self.last_modified(i)
            i.sets = self.sets(i)
        return self.render_to_response({'items': items, 'metadataPrefix': 'oai_dc'})

    def get_record(self):
        self.template_name = 'django_oaipmh/get_record.xml'

        item_identifier = self.request.GET.get('identifier', None)
        if item_identifier is None:
            return self.error('badArgument',
                ' The request includes illegal arguments or is missing required arguments.')
        try:
            item = self.item(item_identifier)
        except Exception:
            return self.error('idDoesNotExist',
                'The value of the identifier argument is unknown or illegal in this repository.')

        item.identifier = self.oai_identifier(item)
        item.record_identifier = self.record_identifier(item)
        item.last_modified = self.last_modified(item)
        item.sets = self.sets(item)

        return self.render_to_response({'item': item})

    def error(self, code, text):
        # TODO: HTTP error response code? maybe 400 bad request?
        # NOTE: may need to revise, could have multiple error codes/messages
        self.template_name = 'django_oaipmh/error.xml'
        return self.render_to_response({
            'error_code': code,
            'error': text,
        })

    # HTTP GET request: determine OAI verb and hand off to appropriate
    # method
    def get(self, request, *args, **kwargs):
        self.request = request   # store for access in other functions

        self.oai_verb = request.GET.get('verb', None)

        if self.oai_verb == 'Identify':
            return self.identify()

        if self.oai_verb == 'ListIdentifiers':
            return self.list_identifiers()

        if self.oai_verb == 'ListRecords':
            return self.list_records()

        if self.oai_verb == 'ListMetadataFormats':
            return self.list_metadata_formats()

        if self.oai_verb == 'ListSets':
            return self.list_sets()

        if self.oai_verb == 'GetRecord':
            return self.get_record()

        else:
            # if no verb = bad request response

            if self.oai_verb is None:
                error_msg = 'The request did not provide any verb.'
            else:
                error_msg = 'The verb "%s" is illegal' % self.oai_verb
            return self.error('badVerb', error_msg)
