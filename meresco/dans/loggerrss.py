## begin license ##
# 
# "Meresco Components" are components to build searchengines, repositories
# and archives, based on "Meresco Core". 
# 
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2011 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2011-2012 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2011 Stichting Kennisnet http://www.kennisnet.nl
# 
# This file is part of "Meresco Components"
# 
# "Meresco Components" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# "Meresco Components" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with "Meresco Components"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# 
## end license ##

from xml.sax.saxutils import escape as xmlEscape
from cgi import parse_qs
from urlparse import urlsplit
from meresco.core import Observable
from meresco.components.sru.sruparser import SruMandatoryParameterNotSuppliedException
from meresco.components.http import utils as httputils
from cqlparser.cqlparser import parseString as CQLParseException

class BadRequestException(Exception):
    pass

class LoggerRSS(Observable):

    def __init__(self, title, description, link, maximumRecords=20):
        Observable.__init__(self)
        self._title = title
        self._description = description
        self._link = link
        self._maximumRecords = maximumRecords

    def handleRequest(self, RequestURI='', **kwargs):        
        yield httputils.okRss
        yield """<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>"""
        try:
            Scheme, Netloc, Path, Query, Fragment = urlsplit(RequestURI)
            arguments = parse_qs(Query)
            maximumRecords = int(arguments.get('maximumRecords', [self._maximumRecords])[0])
            rId = arguments.get('repositoryId', [''])[0] #['']
            if rId =='' or not rId:
                raise BadRequestException('Invalid repositoryId parameter.') 

        except (SruMandatoryParameterNotSuppliedException, BadRequestException, CQLParseException), e:
            yield '<title>ERROR %s</title>' % xmlEscape(self._title)
            yield '<link>%s</link>' % xmlEscape(self._link)
            yield "<description>An error occurred '%s'</description>" % xmlEscape(str(e))
            yield """</channel></rss>"""
            raise StopIteration()
        
        yield '<title>%s</title>' % xmlEscape(self._title)
        yield '<description>%s</description>' % xmlEscape(self._description + rId)
        yield '<link>%s</link>' % xmlEscape(self._link)

        yield self._yieldLogResults(rId=rId, maxlines=maximumRecords)

        yield """</channel>"""
        yield """</rss>"""
  
    def _yieldLogResults(self, rId=None, maxlines=10):
        yield self.call.getLogLinesAsRssItems(rId, maxlines) #self.call.getLogLinesAsXml()