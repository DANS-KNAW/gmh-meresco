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
from seecr.test.utils import getRequest
from meresco.xml import xpath
from lxml import etree
from meresco.servers.gateway.gatewayserver import NORMALISED_DOC_NAME

class GatewayTest(IntegrationTestCase):

    def testOai(self):
        header, body = getRequest(self.gatewayPort, '/oaix', arguments=dict(verb='ListRecords', metadataPrefix=NORMALISED_DOC_NAME))
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        # print "OAIX body:", etree.tostring(body)
        records = xpath(body, '//oai:record')
        self.assertEqual(18, len(records))

        deletes = xpath(body, '//oai:record[oai:header/@status = "deleted"]')
        self.assertEqual(2, len(deletes))

    def testOaiIdentify(self):
        header, body = getRequest(self.gatewayPort, '/oaix', arguments=dict(verb='Identify'))
        # print "Identify body:", etree.tostring(body)
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        adminEmail = xpath(body, '//oai:Identify/oai:adminEmail/text()')
        self.assertEqual("harvester@dans.knaw.nl", adminEmail[0])

    def testOaixInfo(self):
        header, body = getRequest(self.gatewayPort, '/oaix/info/index')
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8', header)
        # print "testOaixInfo:", etree.tostring(body)
        self.assertTrue('normdoc' in etree.tostring(body))
