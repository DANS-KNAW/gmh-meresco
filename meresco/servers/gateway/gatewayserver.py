## begin license ##
#
# Drents Archief beoogt het Drents erfgoed centraal beschikbaar te stellen.
#
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015-2016 Seecr (Seek You Too B.V.) http://seecr.nl
#
# This file is part of "Drents Archief"
#
# "Drents Archief" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Drents Archief" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Drents Archief"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

from meresco.components import XmlPrintLxml, RewritePartname, XmlXPath, FilterMessages, PeriodicCall, Schedule, XmlParseLxml
from meresco.components.http import BasicHttpHandler, ObservableHttpServer, PathFilter, Deproxy, IpFilter
from meresco.components.log import ApacheLogWriter, HandleRequestLog, LogCollector, LogComponent
from meresco.components.sru import SruRecordUpdate

from meresco.core import Observable
from meresco.core.alltodo import AllToDo
from meresco.core.processtools import setSignalHandlers, registerShutdownHandler

from meresco.oai import OaiJazz, OaiPmh, SuspendRegister, OaiAddDeleteRecordWithPrefixesAndSetSpecs
from meresco.oai.info import OaiInfo

from meresco.xml import namespaces

from os import makedirs
from os.path import dirname, abspath, join, isdir

from seecr.utils import DebugPrompt

from sys import stdout

from weightless.core import be, consume
from weightless.io import Reactor

from storage import StorageComponent
from storage.storageadapter import StorageAdapter
from storage.storagecomponent import HashDistributeStrategy, DefaultStrategy

from meresco.xml.namespaces import namespaces

from meresco.dans.storagesplit import Md5HashDistributeStrategy
from meresco.dans.xmlvalidator import Validate
from meresco.dans.logger import Logger # Normalisation Logger.
from meresco.dans.normalisedidl import NormaliseDIDL
from meresco.dans.normalisemods import NormaliseMODS
from meresco.dans.addparttodocument import AddMetadataDocumentPart

# from meresco.dans.metapartconverter import AddMetadataNamespace
# from meresco.dans.longconverter import NormaliseOaiRecord


NORMALISED_DOC_NAME = 'normdoc'


namespacesMap = {
    'dip' : 'urn:mpeg:mpeg21:2005:01-DIP-NS',
    'gal': "info:eu-repo/grantAgreement",
    'hbo': "info:eu-repo/xmlns/hboMODSextension",
    'wmp': "http://www.surfgroepen.nl/werkgroepmetadataplus",
}

def main(reactor, port, statePath, **ignored):

    oaiSuspendRegister = SuspendRegister()
    oaiJazz = be((OaiJazz(join(statePath, 'oai'), alwaysDeleteInPrefixes=[NORMALISED_DOC_NAME]),
        (oaiSuspendRegister,)
    ))

    normLogger = Logger(join(statePath, 'normlogger'))

    # strategie = HashDistributeStrategy() # filename (=partname) is also hashed: difficult to read by human eye...
    strategie = Md5HashDistributeStrategy()

    storeComponent = StorageComponent(join(statePath, 'store'), strategy=strategie, partsRemovedOnDelete=[NORMALISED_DOC_NAME])

    return \
    (Observable(),
        # (scheduledCommitPeriodicCall,),
        # (DebugPrompt(reactor=reactor, port=port+1, globals=locals()),),
        (ObservableHttpServer(reactor=reactor, port=port),
            (BasicHttpHandler(),
                (IpFilter(allowedIps=['127.0.0.1']),
                    (PathFilter('/oaix', excluding=['/oaix/info']),
                        (OaiPmh(repositoryName='Gateway',
                                adminEmail='harvester@dans.knaw.nl',
                                supportXWait=True,
                                batchSize=2000 # Override default batch size of 200.
                            ),
                            (oaiJazz,),
                            (oaiSuspendRegister,),
                            (StorageAdapter(),
                                (storeComponent,),
                            ),
                        )
                    ),
                    (PathFilter('/oaix/info'),
                        (OaiInfo(reactor=reactor, oaiPath='/oai'),
                            (oaiJazz,),
                        )
                    ),
                ),
                (PathFilter('/update'),
                    (SruRecordUpdate(sendRecordData=False, logErrors=True,),
                        (FilterMessages(allowed=['delete']),
                            (storeComponent,),
                            (oaiJazz,),
                        ),
                        (FilterMessages(allowed=['add']),
                            # (LogComponent("LXML:"),),
                            (Validate([('OAI-PMH header','//oai:header', 'OAI-PMH-header.xsd'), ('DIDL container','//didl:DIDL', 'didl.xsd'), ('MODS metadata', '//mods:mods', 'mods-3-6.xsd')]),
                                # (LogComponent("VALIDATED:"),),
                                (AddMetadataDocumentPart(partName='normdoc', fromKwarg='lxmlNode'),
                                    (NormaliseDIDL(nsMap=namespacesMap, fromKwarg='lxmlNode'), # Normalise DIDL in partname=normdoc metadata
                                        (normLogger,),
                                        (NormaliseMODS(nsMap=namespacesMap, fromKwarg='lxmlNode'), # Normalise MODS in partname=normdoc metadata
                                            (normLogger,),
                                            (XmlPrintLxml(fromKwarg='lxmlNode', toKwarg='data'),
                                                (RewritePartname(NORMALISED_DOC_NAME), # Rename converted part.
                                                    (storeComponent,), # Store converted/renamed part.
                                                )
                                            ),
                                            (OaiAddDeleteRecordWithPrefixesAndSetSpecs(metadataPrefixes=[NORMALISED_DOC_NAME]),
                                                (oaiJazz,),
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )

def startServer(port, stateDir, **kwargs):
    setSignalHandlers()
    print 'Firing up Gateway Server.'
    statePath=abspath(stateDir)
    isdir(statePath) or makedirs(statePath)

    reactor = Reactor()
    dna = main(
            reactor=reactor,
            port=port,
            statePath=statePath,
            **kwargs
        )
    server = be(dna)
    consume(server.once.observer_init())

    registerShutdownHandler(statePath=statePath, server=server, reactor=reactor, shutdownMustSucceed=False)

    print 'Ready to rumble at %s' % port
    stdout.flush()
    reactor.loop()

