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

from meresco.oai import OaiPmh, OaiDownloadProcessor, UpdateAdapterFromOaiDownloadProcessor, OaiJazz, OaiBranding, OaiProvenance, OaiAddDeleteRecordWithPrefixesAndSetSpecs


from seecr.utils import DebugPrompt
from storage import StorageComponent

from meresco.xml import namespaces

from storage.storageadapter import StorageAdapter

from meresco.dans.nl_didl_combined import NL_DIDL_combined
from meresco.dans.storagesplit import Md5HashDistributeStrategy
from meresco.dans.writedeleted import ResurrectTombstone, WriteTombstone
from meresco.servers.gateway.gatewayserver import NORMALISED_DOC_NAME
from meresco.dans.loggerrss import LoggerRSS
from meresco.dans.logger import Logger # Normalisation Logger.

NL_DIDL_NORMALISED_PREFIX = 'nl_didl_norm'
NL_DIDL_COMBINED_PREFIX = 'nl_didl_combined'

NAMESPACEMAP = namespaces.copyUpdate({
    'dip' : 'urn:mpeg:mpeg21:2005:01-DIP-NS',
    'gal': "info:eu-repo/grantAgreement",
    'hbo': "info:eu-repo/xmlns/hboMODSextension",
    'wmp': "http://www.surfgroepen.nl/werkgroepmetadataplus",
    'norm'  : 'http://dans.knaw.nl/narcis/normalized',
})


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
                    (FilterMessages(allowed=['add']), #TODO: NL_DIDL_COMBINED_PREFIX formaat aanmaken en naar storage schrijven.
                        # (LogComponent("ADD"),),

                        (XmlXPath(['//document:document/document:part[@name="normdoc"]/text()'], fromKwarg='lxmlNode', toKwarg='data', namespaces=NAMESPACEMAP),
                            # (LogComponent("NORMDOC"),),
                            (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                                (RewritePartname(NL_DIDL_NORMALISED_PREFIX), # Hernoemt partname van 'record' naar "metadata".
                                    (XmlPrintLxml(fromKwarg="lxmlNode", toKwarg="data", pretty_print=True),
                                        (storageComponent,) # Schrijft oai:metadata (=origineel) naar storage.
                                    )
                                )
                            ),
# TODO: Setspecs van een record overnemen en toevoegen.
                            (OaiAddDeleteRecordWithPrefixesAndSetSpecs(setSpecs=['TODO'], metadataPrefixes=[ 'metadata', NL_DIDL_NORMALISED_PREFIX, NL_DIDL_COMBINED_PREFIX ]
                                    # ('metadata', 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didmodel.xsd', 'urn:mpeg:mpeg21:2002:02-DIDL-NS'),
                                    # (NL_DIDL_NORMALISED_PREFIX, '', 'http://gh.kb-dans.nl/normalised/v0.9/'),
                                    # (NL_DIDL_COMBINED_PREFIX, '', 'http://gh.kb-dans.nl/combined/v0.9/') ]
                                ),
                                (LogComponent("addOaiRecord:"),),
                                (storageComponent,),
                                (oaiJazz,) # Assert partNames header and meta are available from storage!
                            ) #! OaiAddRecord
                            # (OaiAddDeleteRecordWithPrefixesAndSetSpecs(metadataPrefixes=[
                            #         ('metadata', 'http://standards.iso.org/ittf/PubliclyAvailableStandards/MPEG-21_schema_files/did/didmodel.xsd', 'urn:mpeg:mpeg21:2002:02-DIDL-NS'),
                            #         # (NL_DIDL_NORMALISED_PREFIX, '', 'http://gh.kb-dans.nl/normalised/v0.9/'),
                            #         # (NL_DIDL_COMBINED_PREFIX, '', 'http://gh.kb-dans.nl/combined/v0.9/')
                            #     ]),
                            #     (storageComponent,),
                            #     (oaiJazz,) # Assert partNames header and meta are available from storage!
                            # ) #! OaiAddRecord

                        ),


                        (XmlXPath(['//document:document/document:part[@name="record"]/text()'], fromKwarg='lxmlNode', toKwarg='data', namespaces=NAMESPACEMAP),
                            (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                                # TODO: Check indien conversies misgaan, dat ook de meta en header part niet naar storage gaan: geen 1 part als het even kan...
                                # Schrijf 'header' partname naar storage:
                                (XmlXPath(['/oai:record/oai:header'], fromKwarg='lxmlNode', namespaces=NAMESPACEMAP),
                                    (RewritePartname("header"),
                                        (XmlPrintLxml(fromKwarg="lxmlNode", toKwarg="data", pretty_print=True),
                                            (storageComponent,) # Schrijft OAI-header naar storage.
                                        )
                                    )
                                )
                            )
                        ),

                        (XmlXPath(['//document:document/document:part[@name="record"]/text()'], fromKwarg='lxmlNode',
                               toKwarg='data', namespaces=NAMESPACEMAP),
                            (XmlParseLxml(fromKwarg='data', toKwarg='lxmlNode'),
                                (NL_DIDL_combined(nsMap=NAMESPACEMAP),
                                    # Create combined format from stored metadataPart and normalized part.
                                    (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'),  # Convert it to plaintext
                                        (RewritePartname(NL_DIDL_COMBINED_PREFIX),  # Rename combined partName
                                            (storageComponent,)  # Write combined partName to storage
                                        )
                                    )
                                ),
                            )
                        ),

                        (XmlXPath(['//document:document/document:part[@name="meta"]/text()'], fromKwarg='lxmlNode', toKwarg='data', namespaces=NAMESPACEMAP),
                            (RewritePartname("meta"),
                                (storageComponent,) # Schrijft harvester 'meta' data naar storage.
                            )
                        )
                    ),

                    (FilterMessages(allowed=['add']),
                        # (LogComponent("UnDelete"),),
                        (ResurrectTombstone(),
                            (storageComponent,),
                        )
                    )
                )
            )
        )
    )




def main(reactor, port, statePath, gatewayPort, quickCommit=False, **ignored):


    strategie = Md5HashDistributeStrategy()
    storage = StorageComponent(join(statePath, 'store'), strategy=strategie, partsRemovedOnDelete=[NL_DIDL_NORMALISED_PREFIX, NL_DIDL_COMBINED_PREFIX, 'metadata'])

    oaiJazz = OaiJazz(join(statePath, 'oai'))
    oaiJazz.updateMetadataFormat("metadata", "http://didl.loc.nl/didl.xsd", NAMESPACEMAP.didl) #TODO: Use correct schema-locations and namespaces.
    oaiJazz.updateMetadataFormat(NL_DIDL_COMBINED_PREFIX, "http://combined.schema.nl", "http://gh.kb-dans.nl/combined/v0.9/")
    oaiJazz.updateMetadataFormat(NL_DIDL_NORMALISED_PREFIX, "http://norm.schema.nl", NAMESPACEMAP.norm)

    normLogger = Logger(join(statePath, '..', 'gateway', 'normlogger'))


    periodicGateWayDownload = PeriodicDownload(
        reactor,
        host='localhost',
        port=gatewayPort,
        schedule=Schedule(period=1 if quickCommit else 10), # WST: Interval in seconds before sending a new request to the GATEWAY in case of an error while processing batch records.(default=1). IntegrationTests need 1 second! Otherwise tests will fail!
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

                # (PathFilter(["/oai"]),
                #     (OaiPmh(repositoryName="NARCIS OAI-pmh", adminEmail="narcis@dans.knaw.nl", externalUrl="http://oai.narcis.nl"),
                #         (oaiJazz,),
                #         (StorageAdapter(),
                #             (storage,)
                #         ),
                #         (OaiBranding(
                #             url="http://www.narcis.nl/images/logos/logo-knaw-house.gif",
                #             link="http://oai.narcis.nl",
                #             title="Narcis - The gateway to scholarly information in The Netherlands"),
                #         ),
                #         (OaiProvenance(
                #             nsMap=NAMESPACEMAP,
                #             baseURL=('meta', '//meta:repository/meta:baseurl/text()'),
                #             harvestDate=('meta', '//meta:record/meta:harvestdate/text()'),
                #             metadataNamespace=('meta', '//meta:record/meta:metadataNamespace/text()'),
                #             identifier=('header','//oai:identifier/text()'),
                #             datestamp=('header', '//oai:datestamp/text()')
                #             ),
                #             (storage,)
                #         )
                #     )
                # ),



# TODO: Verb=Identify op orde
                (PathFilter('/oai'),
                    (OaiPmh(
                            repositoryName="NARCIS OAI-pmh",
                            adminEmail="narcis@dans.knaw.nl",
                            externalUrl="http://oai.narcis.nl",
                            batchSize=200,
                            supportXWait=False
                        ),
                        (oaiJazz, ),
                        # (oaiSuspendRegister, ), #TODO: Waarom schrijven naar dit 'SuspendRegister"? Dit is code aangeleverd door Seecr?!
                        (RetrieveToGetDataAdapter(),
                            (storage,),
                        ),
                        (OaiBranding(
                            url="http://www.narcis.nl/images/logos/logo-knaw-house.gif",
                            link="http://oai.narcis.nl",
                            title="Narcis - The gateway to scholarly information in The Netherlands"),
                        ),
                    )
                ),



                (PathFilter('/rss'),
                    (LoggerRSS( title = 'Gemeenschappelijke Harvester DANS-KB', description = 'Harvester normalisation log for: ', link = 'http://rss.gharvester.dans.knaw.nl/rss', maximumRecords = 30),
                        (normLogger,
                            (storage,)
                        )
                    )
                ),

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
