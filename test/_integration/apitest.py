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


    def testRSS(self): # From GMH21 OK
        header, body = getRequest(self.apiPort, '/rss', dict(repositoryId='kb_tst', maximumRecords=10)) #, startRecord='1'
        # print "RSS body:", etree.tostring(body)   
        self.assertEquals(6, len(xpath(body, "/rss/channel/item/description")))
        self.assertEqual('GMH DANS-KB Normalisationlog Syndication', xpathFirst(body, '//channel/title/text()'))
        self.assertEqual('DIDL: HumanStartPage descriptor found in depricated dip namespace.\n', xpathFirst(body, '//item/description/text()'))


    def testOai(self): # NOTIN GMH21
        header, body = getRequest(self.apiPort, '/oai', dict(verb="ListRecords", metadataPrefix=NL_DIDL_NORMALISED_PREFIX))
        # print "OAI body:", etree.tostring(body) #
        records = xpath(body, '//oai:record/oai:metadata')
        # self.assertEqual(11, len(records))
        # self.assertEqual('http://www.openarchives.org/OAI/2.0/oai_dc/', xpathFirst(body, '//oaiprov:provenance/oaiprov:originDescription/oaiprov:metadataNamespace/text()'))
        
    # def testOaiSubject(self):
    #     header, body = getRequest(self.apiPort, '/oai', dict(verb="GetRecord", identifier = "meresco:record:1",   metadataPrefix="oai_dc"))
    #     self.assertEqual('Search', xpathFirst(body, '//dc:subject/text()'))
        

    def testOaiIdentify(self): # From GMH21 OK
        header, body = getRequest(self.apiPort, '/oai', dict(verb="Identify"))
        # print "OAI Identify:", etree.tostring(body)
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEqual('Gemeenschappelijke Metadata Harvester DANS-KB', xpathFirst(body, '//oai:Identify/oai:repositoryName/text()'))
        self.assertEqual('harvester@dans.knaw.nl', xpathFirst(body, '//oai:Identify/oai:adminEmail/text()'))
        self.assertEqual('Gemeenschappelijke Metadata Harvester (GMH) van DANS en de KB', testNamespaces.xpathFirst(body, '//oai:Identify/oai:description/oaibrand:branding/oaibrand:collectionIcon/oaibrand:title/text()'))


    def testOaiListMetadataFormats(self): # From GMH21 OK
        header, body = getRequest(self.apiPort, '/oai', dict(verb="ListMetadataFormats"))
        # print 'ListMetadataFormats:', etree.tostring(body)
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals(3, len(xpath(body, "//oai:ListMetadataFormats/oai:metadataFormat")))
        self.assertEqual('metadata', xpath(body, "//oai:ListMetadataFormats/oai:metadataFormat[1]/oai:metadataPrefix/text()")[0])
        self.assertEqual('nl_didl_combined', xpath(body, "//oai:ListMetadataFormats/oai:metadataFormat[2]/oai:metadataPrefix/text()")[0])
        self.assertEqual('nl_didl_norm', xpath(body, "//oai:ListMetadataFormats/oai:metadataFormat[3]/oai:metadataPrefix/text()")[0])


    def testOaiListSets(self): # From GMH21 TODO
        header, body = getRequest(self.apiPort, '/oai', dict(verb="ListSets"))
        # print "ListSets", etree.tostring(body)
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        # self.assertEquals(7, len(body.OAI_PMH.ListSets.set))
        # self.assertEquals('kb', body.OAI_PMH.ListSets.set[0].setSpec)        
        # self.assertEqual({'publication','openaire','oa_publication','ec_fundedresources','thesis','dataset'}, set(xpath(body, '//oai:setSpec/text()')))

    # def testOaiListSets(self):
    #     header, body = getRequest(reactor, port, '/oai', {'verb': 'ListSets'})
    #     # print 'ListSets:', body.xml()
    #     self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
    #     self.assertEquals(7, len(body.OAI_PMH.ListSets.set))
    #     self.assertEquals('kb', body.OAI_PMH.ListSets.set[0].setSpec)


    def testDeleteRecord(self): # From GMH21 TODO
        header, body = getRequest(self.apiPort, '/oai', dict(verb="GetRecord", metadataPrefix='metadata', identifier='kb_tst:GMH:05')) #kb_tst:GMH:06
        # print "GetRecord DELETED", etree.tostring(body)
        # self.assertEquals('deleted', xpath(body, "//oai:GetRecord/oai:record[1]/oai:header/@status")[0])


    def testProvenanceMetaDataNamespace(self): # From GMH21 TODO
        header, body = getRequest(self.apiPort, '/oai', dict(verb="ListRecords", metadataPrefix='metadata'))
        # print "ListRecords, nl_didl_norm:", etree.tostring(body)
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals(16, len(xpath(body, "//oai:ListRecords/oai:record")))

        # for record in xpath(body, "//oai:ListRecords/oai:record"):
        #     if not str(record.header.status) == 'deleted':
        #         # print 'metadataNamespace:', str(record.about.provenance.originDescription.metadataNamespace)
        #         self.assertTrue('mods' in str(record.about.provenance.originDescription.metadataNamespace))

