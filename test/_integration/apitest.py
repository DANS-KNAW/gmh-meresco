## begin license ##
#
# "Meresco Examples" is a project demonstrating some of the
# features of various components of the "Meresco Suite".
# Also see http://meresco.org.
#
# Copyright (C) 2016 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Meresco Examples"
#
# "Meresco Examples" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Meresco Examples" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Meresco Examples"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from seecr.test import IntegrationTestCase
from seecr.test.utils import getRequest, sleepWheel, htmlXPath
from meresco.xml import xpathFirst, xpath, namespaces
from lxml import etree
from lxml.etree import tostring, fromstring

NL_DIDL_NORMALISED_PREFIX = 'nl_didl_norm'


# TODO: create UnitTestCase for o.a. writeDelete / unDelete
# TODO: SRU-throttle mogelijkheden uitzoeken.

testNamespaces = namespaces.copyUpdate({'oaibrand':'http://www.openarchives.org/OAI/2.0/branding/',
    'prs'    : 'http://www.onderzoekinformatie.nl/nod/prs',
    'proj'   : 'http://www.onderzoekinformatie.nl/nod/act',
    'org'    : 'http://www.onderzoekinformatie.nl/nod/org',
    'long'   : 'http://www.knaw.nl/narcis/1.0/long/',
    'short'  : 'http://www.knaw.nl/narcis/1.0/short/',
    'mods'   : 'http://www.loc.gov/mods/v3',
    'didl'   : 'urn:mpeg:mpeg21:2002:02-DIDL-NS',
    'norm'   : 'http://dans.knaw.nl/narcis/normalized',
    })

class ApiTest(IntegrationTestCase):



    def testOai(self):
        header, body = getRequest(self.apiPort, '/oai', dict(verb="ListRecords", metadataPrefix=NL_DIDL_NORMALISED_PREFIX))
        # print "OAI body:", etree.tostring(body) #
        records = xpath(body, '//oai:record/oai:metadata')
        # self.assertEqual(11, len(records))
        # self.assertEqual('http://www.openarchives.org/OAI/2.0/oai_dc/', xpathFirst(body, '//oaiprov:provenance/oaiprov:originDescription/oaiprov:metadataNamespace/text()'))
        
    # def testOaiSubject(self):
    #     header, body = getRequest(self.apiPort, '/oai', dict(verb="GetRecord", identifier = "meresco:record:1",   metadataPrefix="oai_dc"))
    #     self.assertEqual('Search', xpathFirst(body, '//dc:subject/text()'))
        

    def testOaiIdentify(self):
        header, body = getRequest(self.apiPort, '/oai', dict(verb="Identify"))
        # print "OAI Identify:", etree.tostring(body)
        self.assertEqual('NARCIS OAI-pmh', xpathFirst(body, '//oai:Identify/oai:repositoryName/text()'))
        self.assertEqual('Narcis - The gateway to scholarly information in The Netherlands', testNamespaces.xpathFirst(body, '//oai:Identify/oai:description/oaibrand:branding/oaibrand:collectionIcon/oaibrand:title/text()'))

    def testOaiListSets(self):
        header, body = getRequest(self.apiPort, '/oai', dict(verb="ListSets"))
        # print "ListSets", etree.tostring(body)
        # self.assertEqual({'publication','openaire','oa_publication','ec_fundedresources','thesis','dataset'}, set(xpath(body, '//oai:setSpec/text()')))

    def testOaiListMetadataFormats(self):
        header, body = getRequest(self.apiPort, '/oai', dict(verb="ListMetadataFormats"))
        # print "ListMetadataFormats", etree.tostring(body)
        # self.assertEqual({'oai_dc'}, set(xpath(body, '//oai:metadataFormat/oai:metadataPrefix/text()')))


    def testRSS(self): #TODO: Find out why DIFFER has two similair entries in the lohfile
        header, body = getRequest(self.apiPort, '/rss', dict(repositoryId='beeldengeluid', maximumRecords=10)) #, startRecord='1'
        # print "RSS body:", etree.tostring(body)
        descriptions = xpath(body, "/rss/channel/item/description")        
        self.assertEquals(1, len(descriptions))
        self.assertEqual('Gemeenschappelijke Harvester DANS-KB', xpathFirst(body, '//channel/title/text()'))
        self.assertEqual('MODS: mods is not a valid RFC3066 language code.\n', xpathFirst(body, '//item/description/text()'))
