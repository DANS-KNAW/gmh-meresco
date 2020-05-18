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

class ResolverTest(IntegrationTestCase):

    def testOaiIdentify(self):
        header, body = getRequest(self.resolverPort, '/', arguments=dict(identifier='urn:nbn:nl:ui:39-ae86436a9031f6f287b2fdc6f54e3fe6'))
        self.assertEqual('HTTP/1.0 200 OK\r\nContent-Type: text/plain; charset=utf-8', header)
        self.assertEqual('<html><body><p>Resolver Server</p></body></html>', etree.tostring(body))
