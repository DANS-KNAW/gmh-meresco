#-*- coding: utf-8 -*-
## begin license ##
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) Data Archiving and Networked Services (DANS) http://dans.knaw.nl
#
# This file is part of "NARCIS Index"
#
# "NARCIS Index" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "NARCIS Index" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "NARCIS Index"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

import sys
from sys import stdout
from os.path import join, dirname, abspath

from weightless.core import be, consume
from weightless.io import Reactor


from meresco.core import Observable
from meresco.core.alltodo import AllToDo
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler

from meresco.components import RenameFieldForExact, PeriodicDownload, XmlPrintLxml, XmlXPath, FilterMessages, RewritePartname, XmlParseLxml, CqlMultiSearchClauseConversion, PeriodicCall, Schedule, XsltCrosswalk, RetrieveToGetDataAdapter #, Rss, RssItem
from meresco.components.http import ObservableHttpServer, BasicHttpHandler, PathFilter, Deproxy
from meresco.components.log import LogCollector, ApacheLogWriter, HandleRequestLog, LogCollectorScope, QueryLogWriter, DirectoryLog, LogFileServer, LogComponent

from meresco.oai import OaiPmh, OaiDownloadProcessor, UpdateAdapterFromOaiDownloadProcessor, OaiJazz, OaiBranding, OaiProvenance#, OaiAddDeleteRecordWithPrefixesAndSetSpecs


from seecr.utils import DebugPrompt
from storage import StorageComponent

from meresco.xml import namespaces

from storage.storageadapter import StorageAdapter

from meresco.dans.nldidlcombined import NlDidlCombined
from meresco.dans.storagesplit import Md5HashDistributeStrategy
from meresco.dans.writedeleted import ResurrectTombstone, WriteTombstone
from meresco.servers.gateway.gatewayserver import NORMALISED_DOC_NAME
from meresco.dans.loggerrss import LoggerRSS
from meresco.dans.logger import Logger # Normalisation Logger.
from meresco.seecr.oai import OaiAddDeleteRecordWithPrefixesAndSetSpecs, OaiAddRecord
from meresco.dans.xlsserver import XlsServer

NL_DIDL_NORMALISED_PREFIX = 'nl_didl_norm'
NL_DIDL_COMBINED_PREFIX = 'nl_didl_combined'

NAMESPACEMAP = namespaces.copyUpdate({
    'dip'           : 'urn:mpeg:mpeg21:2005:01-DIP-NS',
    'gal'           : 'info:eu-repo/grantAgreement',
    'hbo'           : 'info:eu-repo/xmlns/hboMODSextension',
    'wmp'           : 'http://www.surfgroepen.nl/werkgroepmetadataplus',
    'gmhnorm'       : 'http://gh.kb-dans.nl/normalised/v0.9/',
    'gmhcombined'   : 'http://gh.kb-dans.nl/combined/v0.9/',
    'meta' : 'http://meresco.org/namespace/harvester/meta',
    'oai': 'http://www.openarchives.org/OAI/2.0/'

})

myPath = dirname(abspath(__file__))
# dynamicHtmlPath = join(myPath, 'controlpanel', 'html', 'dynamic')
# staticHtmlPath = join(myPath, 'controlpanel', 'html', 'static')

def createDownloadHelix(reactor, periodicDownload, oaiDownload, storageComponent, oaiJazz):
    return \
    (periodicDownload, # Scheduled connection to a remote (response / request)...
        (XmlParseLxml(fromKwarg="data", toKwarg="lxmlNode", parseOptions=dict(huge_tree=True, remove_blank_text=True)), # Convert from plain text to lxml-object.
            (oaiDownload, # Implementation/Protocol of a PeriodicDownload...
                (UpdateAdapterFromOaiDownloadProcessor(), # Maakt van een SRU update/delete bericht (lxmlNode) een relevante message: 'delete' of 'add' message.
                    (FilterMessages(['delete']), # Filtert delete messages
                        # (LogComponent("Delete Update"),),
                        (storageComponent,), # Delete from storage
                        (oaiJazz,), # Delete from OAI-pmh repo
                        # Write a 'deleted' part to the storage, that holds the (Record)uploadId.
                        (WriteTombstone(),
                            (storageComponent,),
                        )
                    ),
                    (FilterMessages(allowed=['add']),
                        # (LogComponent("ADD"),),

                        (XmlXPath(['//document:document/document:part[@name="normdoc"]/text()'], fromKwarg='lxmlNode', toKwarg='data', namespaces=NAMESPACEMAP),
                            # (LogComponent("NORMDOC"),),
                            (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                                (RewritePartname(NL_DIDL_NORMALISED_PREFIX), # Hernoemt partname van 'record' naar "metadata".
                                    (XmlPrintLxml(fromKwarg="lxmlNode", toKwarg="data", pretty_print=True),
                                        (storageComponent,) # Schrijft oai:metadata (=origineel) naar storage.
                                    )
                                )
                            )
                        ),

                        (XmlXPath(['//document:document/document:part[@name="record"]/text()'], fromKwarg='lxmlNode', toKwarg='data', namespaces=NAMESPACEMAP),
                            (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                                # TODO: Check indien conversies misgaan, dat ook de meta en header part niet naar storage gaan: geen enkel part als het even kan...
                                # Schrijf 'header' partname naar storage:
                                (XmlXPath(['/oai:record/oai:header'], fromKwarg='lxmlNode', namespaces=NAMESPACEMAP),
                                    (RewritePartname("header"),
                                        (XmlPrintLxml(fromKwarg="lxmlNode", toKwarg="data", pretty_print=True),
                                            (storageComponent,) # Schrijft OAI-header naar storage.
                                        )
                                    )
                                ),
                                # Schrijf 'metadata' partname naar storage:
                                # Op gharvester21 gaat dit niet goed: Daar is het root element <metadata> in het 'metadata' part, in plaats van <DIDL>.
                                # Liever hier een child::node(), echter gaat deze syntax mis i.c.m. XmlXPath component??
                                (XmlXPath(['/oai:record/oai:metadata/didl:DIDL'], fromKwarg='lxmlNode', namespaces=NAMESPACEMAP),
                                    # (LogComponent("METADATA_PART"),),
                                    (RewritePartname("metadata"),
                                        (XmlPrintLxml(fromKwarg="lxmlNode", toKwarg="data", pretty_print=True),
                                            (storageComponent,) # Schrijft metadata naar storage.
                                        )
                                    )
                                )
                            )
                        ),

                        (XmlXPath(['//document:document/document:part[@name="record"]/text()'], fromKwarg='lxmlNode',
                               toKwarg='data', namespaces=NAMESPACEMAP),
                            (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                                (NlDidlCombined(nsMap=NAMESPACEMAP, fromKwarg='lxmlNode'),
                                    # Create combined format from stored metadataPart and normalized part.
                                    (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'),  # Convert it to plaintext
                                        (RewritePartname(NL_DIDL_COMBINED_PREFIX),  # Rename combined partName
                                            (storageComponent,)  # Write combined partName to storage
                                        )
                                    )
                                )
                            )
                        ),

                        (XmlXPath(['//document:document/document:part[@name="meta"]/text()'], fromKwarg='lxmlNode', toKwarg='data', namespaces=NAMESPACEMAP),
                            (RewritePartname("meta"),
                                (storageComponent,) # Schrijft harvester 'meta' data naar storage.
                            )
                        ),

                        (OaiAddRecord(metadataPrefixes=[('metadata', 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didmodel.xsd', 'urn:mpeg:mpeg21:2002:02-DIDL-NS'),
                                    (NL_DIDL_NORMALISED_PREFIX, '', NAMESPACEMAP.gmhnorm),
                                    (NL_DIDL_COMBINED_PREFIX, '', NAMESPACEMAP.gmhcombined)]), #[(partname, schema, namespace)]
                            # (LogComponent("OaiAddRecord:"),),
                            (storageComponent,),
                            (oaiJazz,) # Assert partNames header and meta are available from storage!
                        ),

                        (ResurrectTombstone(),
                            (storageComponent,),
                        ),                    

                    ),

                    # (FilterMessages(allowed=['add']),
                    #     # (LogComponent("UnDelete"),),
                    #     (ResurrectTombstone(),
                    #         (storageComponent,),
                    #     )
                    # )
                )
            )
        )
    )




def main(reactor, port, statePath, gatewayPort, quickCommit=False, **ignored):


    strategie = Md5HashDistributeStrategy()
    storage = StorageComponent(join(statePath, 'store'), strategy=strategie, partsRemovedOnDelete=[NL_DIDL_NORMALISED_PREFIX, NL_DIDL_COMBINED_PREFIX, 'metadata'])

    oaiJazz = OaiJazz(join(statePath, 'oai'))
    oaiJazz.updateMetadataFormat("metadata", "http://didl.loc.nl/didl.xsd", NAMESPACEMAP.didl)
    oaiJazz.updateMetadataFormat(NL_DIDL_COMBINED_PREFIX, "", NAMESPACEMAP.gmhcombined)
    oaiJazz.updateMetadataFormat(NL_DIDL_NORMALISED_PREFIX, "", NAMESPACEMAP.gmhnorm)

    normLogger = Logger(join(statePath, '..', 'gateway', 'normlogger'))


    periodicGateWayDownload = PeriodicDownload(
        reactor,
        host='localhost',
        port=gatewayPort,
        schedule=Schedule(period=.1 if quickCommit else 10), # WST: Interval in seconds before sending a new request to the GATEWAY in case of an error while processing batch records.(default=1). IntegrationTests need <=1 second! Otherwise tests will fail!
        name='api',
        autoStart=True)

    oaiDownload = OaiDownloadProcessor(
        path='/oaix',
        metadataPrefix=NORMALISED_DOC_NAME,
        workingDirectory=join(statePath, 'harvesterstate', 'gateway'),
        userAgentAddition='ApiServer',
        xWait=True,
        name='api',
        autoCommit=False)


    return \
    (Observable(),
        createDownloadHelix(reactor, periodicGateWayDownload, oaiDownload, storage, oaiJazz),
        (ObservableHttpServer(reactor, port, compressResponse=True),
            (BasicHttpHandler(),
                (PathFilter('/oai'),
                    (OaiPmh(
                            repositoryName="Gemeenschappelijke Metadata Harvester DANS-KB",
                            adminEmail="harvester@dans.knaw.nl",
                            externalUrl="http://oai.gharvester.dans.knaw.nl",
                            batchSize=200,
                            supportXWait=False,
                            # preciseDatestamp=False,
                            # deleteInSets=False
                        ),
                        (oaiJazz, ),
                        (RetrieveToGetDataAdapter(),
                            (storage,),
                        ),
                        (OaiBranding(
                            url="https://www.narcis.nl/images/logos/logo-knaw-house.gif", #TODO: Link to a joint-GMH icon...
                            link="https://harvester.dans.knaw.nl",
                            title="Gemeenschappelijke Metadata Harvester (GMH) van DANS en de KB"),
                        ),
                        (OaiProvenance(
                            nsMap=NAMESPACEMAP,
                            baseURL=('meta', '//meta:repository/meta:baseurl/text()'),
                            harvestDate=('meta', '//meta:harvestdate/text()'),
                            metadataNamespace=('meta', '//meta:metadataPrefix/text()'), #TODO: Kan hardcoded in harvester mapper gezet eventueel: <metadataNamespace>urn:mpeg:mpeg21:2002:01-DII-NS</metadataNamespace>?? (storage,) #metadataNamespace=('meta', '//meta:record/meta:metadataNamespace/text()'),
                            identifier=('header','//oai:identifier/text()'),
                            datestamp=('header', '//oai:datestamp/text()')
                            ),  
                            (RetrieveToGetDataAdapter(),
                                (storage,),
                            )
                        )
                    )
                ),
                (PathFilter('/rss'),
                    (LoggerRSS( title = 'GMH DANS-KB Normalisationlog Syndication', description = 'Harvester normalisation log for: ', link = 'http://rss.gharvester.dans.knaw.nl/rss', maximumRecords = 30),
                        (normLogger,
                            (storage,)
                        )
                    )
                ),
                (PathFilter('/xls'),
                    # (LogComponent("XLS-Request:"),),
                    (XlsServer(),)
                )                
            )
        )
    )

def startServer(port, stateDir, gatewayPort, quickCommit=False, **kwargs):
    setSignalHandlers()
    print 'Firing up API Server.'
    statePath = abspath(stateDir)

    reactor = Reactor()
    dna = main(
        reactor=reactor,
        port=port,
        statePath=statePath,
        gatewayPort=gatewayPort,
        quickCommit=quickCommit,
        **kwargs
    )

    server = be(dna)
    consume(server.once.observer_init())

    registerShutdownHandler(statePath=statePath, server=server, reactor=reactor, shutdownMustSucceed=False)

    print "Ready to rumble at %s" % port
    sys.stdout.flush()
    reactor.loop()
