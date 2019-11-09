# -*- coding: utf-8 -*-
# encoding: utf-8
## begin license ##
#
#    Meresco Examples is a project demonstrating some of the features of
#    various Meresco components.
#    Copyright (C) 2007-2008 SURF Foundation. http://www.surf.nl
#    Copyright (C) 2007-2009 Stichting Kennisnet Ict op school.
#       http://www.kennisnetictopschool.nl
#    Copyright (C) 2009 Delft University of Technology http://www.tudelft.nl
#    Copyright (C) 2009 Tilburg University http://www.uvt.nl
#    Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
#
#    This file is part of Meresco Examples.
#
#    Meresco Examples is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    Meresco Examples is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Meresco Examples; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##
from os import getuid

import sys
assert getuid() != 0, "Do not run tests as 'root'"

sys.path.insert(0, "..")

import pdb

from os import system
from sys import exit, exc_info, stdout

from os.path import isdir, isfile

from unittest import main
from random import randint
from time import time
from glob import glob

from weightless.io import Reactor
from weightless.core import Transparent, be, compose
from amara.binderytools import bind_file, bind_string
from meresco_server.server import dna, config

from seecr.test import SeecrTestCase
from utils_local import sleepWheel

#Gebruik oude package voor get/postRequest met reactor.
#Voor loose coupling, zonder Reactor gebruik ze uit de seecr.test package.
from cq2utils import getRequest, postRequest

integrationTempdir = './integration_temp_dir'
reactor = Reactor()


class IntegrationTest(SeecrTestCase):

    def _path(self, subdir):
        return join(self.tempdir, subdir)
        
        
###SRU explainresponse##############
# <?xml version="1.0" encoding="UTF-8"?><srw:explainResponse xmlns:srw="http://www.loc.gov/zing/srw/"
#    xmlns:zr="http://explain.z3950.org/dtd/2.0/">
#     <srw:version>1.1</srw:version>
#     <srw:record>
#         <srw:recordPacking>xml</srw:recordPacking>
#         <srw:recordSchema>http://explain.z3950.org/dtd/2.0/</srw:recordSchema>
#         <srw:recordData>
#             <zr:explain>
#                 <zr:serverInfo protocol="SRU" version="1.1">
#                     <host>localhost</host>
#                     <port>8000</port>
#                     <database>sru</database>
#                 </zr:serverInfo>
#                 <zr:databaseInfo>
#                     <title lang="en" primary="true">SRU Database</title>
#                     <description lang="en" primary="true">Meresco SRU</description>
#                 </zr:databaseInfo>
#             </zr:explain>
#         </srw:recordData>
#     </srw:record>
# </srw:explainResponse>


    def testRSS(self):
        body = self._doQuery({'repositoryId':'kb_tst', 'maximumRecords':'10'}, path="/rss")
        items = [(str(item.guid), str(item.description), str(item.pubDate)) for item in body.rss.channel.item]
    
        # print 'RSS BODY:', body.xml()
        # for item in items:
        #     print '\nRss ITEM:', item
        
        self.assertEquals(6, len(items))
        
    def testOaiListMetadataFormats(self):
        header, body = getRequest(reactor, port, '/oai', {'verb': 'ListMetadataFormats'})
        #print 'ListMetadataFormats:', body.xml()
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals(3, len(body.OAI_PMH.ListMetadataFormats.metadataFormat))
        self.assertEquals('metadata', body.OAI_PMH.ListMetadataFormats.metadataFormat[0].metadataPrefix)
        self.assertEquals('nl_didl_combined', body.OAI_PMH.ListMetadataFormats.metadataFormat[1].metadataPrefix)
        self.assertEquals('nl_didl_norm', body.OAI_PMH.ListMetadataFormats.metadataFormat[2].metadataPrefix)

    def testOaiIdentify(self):
        header, body = getRequest(reactor, port, '/oai', {'verb': 'Identify'})
        #print 'Identify:', body.xml()
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals('Gemeenschappelijke Harvester DANS-KB', body.OAI_PMH.Identify.repositoryName)
        self.assertEquals('harvester@dans.knaw.nl', body.OAI_PMH.Identify.adminEmail)

    def testOaiListSets(self):
        header, body = getRequest(reactor, port, '/oai', {'verb': 'ListSets'})
        #print 'ListSets:', body.xml()
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals(3, len(body.OAI_PMH.ListSets.set))
        self.assertEquals('kb', body.OAI_PMH.ListSets.set[0].setSpec)

    def testProvenanceMetaDataNamespace(self):
        header, body = getRequest(reactor, port, '/oai', {'verb': 'ListRecords', 'metadataPrefix': 'nl_didl_norm'}) #, 'set': 'ir'
        #print 'ListRecords: AANTAL:', len(body.OAI_PMH.ListRecords.record)
        #print 'BODY:', body.xml()

        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals(8, len(body.OAI_PMH.ListRecords.record))

        for record in body.OAI_PMH.ListRecords.record:
            if not str(record.header.status) == 'deleted':
                # print 'metadataNamespace:', str(record.about.provenance.originDescription.metadataNamespace)
                self.assertTrue('mods' in str(record.about.provenance.originDescription.metadataNamespace))
                

    def testOaiSet(self):        
        header, body = getRequest(reactor, port, '/oai', {'verb': 'ListRecords', 'metadataPrefix': 'nl_didl_combined', 'set': 'kb:KB'})
        #print 'ListRecords:', body.xml()
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals(6, len(body.OAI_PMH.ListRecords.record))

    def testOaiGetRecord(self):
        header, body = getRequest(reactor, port, '/oai', {'verb': 'GetRecord', 'metadataPrefix': 'metadata', 'identifier': 'kb_tst:GMH:04'})
        #print body.xml()
        self.assertEquals('HTTP/1.0 200 OK\r\nContent-Type: text/xml; charset=utf-8', header)
        self.assertEquals(1, len(body.OAI_PMH.GetRecord.record))

    def testDeleteRecord(self): 
        header, body = getRequest(reactor, port, '/oai', {'verb': 'GetRecord', 'identifier': 'kb_tst:GMH:05', 'metadataPrefix': 'metadata'})
        #print body.xml()
        self.assertEquals('deleted', body.OAI_PMH.GetRecord.record[0].header.status)

    def _doQuery(self, arguments, path="/rss"):
        #queryArguments = {'version': '1.1', 'operation': 'searchRetrieve', 'sortKeys': 'untokenized.mutatiedatum,,1', 'recordSchema':'meta'} #sort_title_en
        queryArguments = {}
        queryArguments.update(arguments)
        header, body = getRequest(reactor, port, path, queryArguments)
        #print 'HEADER:', header
        #print 'BODY:', body.xml()
        return body


def createDatabase(port):
    recordPacking = 'xml'
    start = time()
    print "Creating database in", integrationTempdir
    sourceFiles = glob('updaterequests/*/*.updateRequest') #integration/
    for updateRequestFile in sorted(sourceFiles):
        print 'Sending:', updateRequestFile
        
        header, body = postRequest(reactor, port, '/update', open(updateRequestFile).read(), parse=False)
        
        if '200 Ok' not in header:
            print 'No 200 Ok response, but:'
            print header
            exit(123)
        if "srw:diagnostics" in body:
            print 'ERROR: Previous .updateRequest caused a "srw:diagnostics". Record has not been processed.'
            # print body
    print "Finished creating database in %s seconds" % (time() - start)

if __name__ == '__main__':
    from sys import argv
    if not '--fast' in argv:
        system('rm -rf ' + integrationTempdir)
        system('mkdir --parents '+ integrationTempdir)

    port = randint(50000, 60000)
    
    server = be(dna(reactor, config['host'], portNumber=port, databasePath=integrationTempdir))
    list(compose(server.once.observer_init()))

    print "Server listening on", config['host'], "at port", port
    print "   - database:", integrationTempdir, "\n"
    
    stdout.flush()

    if '--fast' in argv and isdir(integrationTempdir):
        argv.remove('--fast')
        print "Reusing database in", integrationTempdir
    else:
        createDatabase(port)    
    main()