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
        print "ListMetadataFormats", etree.tostring(body)
        # self.assertEqual({'oai_dc'}, set(xpath(body, '//oai:metadataFormat/oai:metadataPrefix/text()')))


    # def testRSS(self):
    #     header, body = getRequest(self.apiPort, '/rss', dict(query="*", querylabel='MyLabel', sortKeys='untokenized.dateissued,,0', startRecord='4'))
    #     # print "RSS body:", etree.tostring(body)
    #     items = xpath(body, "/rss/channel/item")
    #     self.assertEquals(12, len(items))
    #     self.assertTrue(xpathFirst(body, '//item/link/text()').endswith('Language/nl'))
    #     self.assertEqual({'Paden en stromingen---a historical survey', 'System of wireless base stations employing shadow prices for power load balancing', 'Preface to special issue (Fast reaction - slow diffusion scenarios: PDE approximations and free boundaries)', 'Conditiebepaling PVC', 'Appositie en de interne struktuur van de NP', 'Example Program 2', 'Locatie [Matthijs Tinxgracht 16] te Edam, gemeente Edam-Volendam. Een archeologische opgraving.', u'\u042d\u043a\u043e\u043b\u043e\u0433\u043e-\u0440\u0435\u043a\u0440\u0435\u0430\u0446\u0438\u043e\u043d\u043d\u044b\u0439 \u043a\u043e\u0440\u0438\u0434\u043e\u0440 \u0432 \u0433\u043e\u0440\u043d\u043e\u043c \u0437\u0430\u043f\u043e\u0432\u0435\u0434\u043d\u0438\u043a\u0435 \u0411\u043e\u0433\u043e\u0442\u044b', 'Bennis, Prof.dr. H.J. (Hans)', 'Late-type Giants in the Inner Galaxy', 'Wetenschapswinkel', "The Language Designer's Workbench: Automating Verification of Language Definitions"}, set(xpath(body, "//item/title/text()")))
    #     self.assertEqual({'Abstract van dit document', 'In one aspect, a system is provided. In one embodiment, the system includes a plurality of wireless base stations that are located in a contiguous spatial coverage region of a cellular communication system. Each wireless base station that is configured to generate a coverage pilot beam to enable', 'FransHeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeellllllang', 'Microvariatie; (Generatieve) Syntaxis; Morphosyntaxis; Syntaxis-Semantiek Interface; Dialectologie', 'Abstract', 'Samenvatting', 'Projectomschrijving<br>Ontwikkeling van betrouwbare methoden, procedures\n            en extrapolatiemodellen om de conditie en restlevensduur van in gebruik zijnde\n            PVC-leidingen te bepalen.<br>Beoogde projectopbrengsten<br>- uitwerking van\n            huidige kennis en inzichten m.b.t.', 'De KNAW vervult drie (wettelijke) taken: genootschap van excellente wetenschappers uit\n        alle disciplines; bestuurder van wetenschappelijke onderzoeksinstituten; adviseur van de\n        regering op het gebied van wetenschapsbeoefening. Zijne Majesteit de Koning is beschermheer\n        van de', 'The present thesis describes the issue of\n            "neonatal glucocorticoid treatment and predisposition to\n            cardiovascular disease in rats".', 'This is an example program about Programming with Meresco'}, set(xpath(body, "//item/description/text()")))
    #     self.assertEqual('MyLabel', xpathFirst(body, '//channel/title/text()'))
    #     self.assertEqual('http://www.narcis.nl/dataset/RecordID/oai%3Aeasy.dans.knaw.nl%3Aeasy-dataset%2F44292/Language/nl', xpath(body, '//item[5]/link/text()')[0])
