# -*- coding: utf-8 -*-
## begin license ##
#
# Drents Archief beoogt het Drents erfgoed centraal beschikbaar te stellen.
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012-2014 Stichting Bibliotheek.nl (BNL) http://www.bibliotheek.nl
# Copyright (C) 2015-2016 Drents Archief http://www.drentsarchief.nl
# Copyright (C) 2015 Koninklijke Bibliotheek (KB) http://www.kb.nl
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

from os import listdir
from os.path import join, abspath, dirname, isdir
from time import sleep, time
from traceback import print_exc

from seecr.test.integrationtestcase import IntegrationState
from seecr.test.portnumbergenerator import PortNumberGenerator
from seecr.test.utils import postRequest, sleepWheel

from glob import glob

mydir = dirname(abspath(__file__))
projectDir = dirname(dirname(mydir))

JAVA_BIN="/usr/lib/jvm/jre-1.8.0/bin"
if not isdir(JAVA_BIN):
    JAVA_BIN="/etc/alternatives/jre_1.8.0/bin"

class GmhTestIntegrationState(IntegrationState):
    def __init__(self, stateName, tests=None, fastMode=False):
        IntegrationState.__init__(self, stateName, tests=tests, fastMode=fastMode)

        self.testdataDir = join(dirname(mydir), 'updateRequest')
        self.gatewayPort = PortNumberGenerator.next()
        self.apiPort = PortNumberGenerator.next()
        # self.indexPort = PortNumberGenerator.next()


    def binDir(self):
        return join(projectDir, 'bin')

    def setUp(self):
        self.startGatewayServer()
        self.startApiServer()        
        # self.startIndexServer()
        self.waitForServicesStarted()
        self._createDatabase()
        sleep(0.2)

    def startGatewayServer(self):
        executable = self.binPath('start-gateway')
        self._startServer(
            serviceName='gateway',
            debugInfo=True,
            executable=executable,
            serviceReadyUrl='http://localhost:%s/info/version' % self.gatewayPort,
            cwd=dirname(abspath(executable)),
            port=self.gatewayPort,
            stateDir=join(self.integrationTempdir, 'gateway'),
            waitForStart=False)

    def startIndexServer(self):
        executable = self.binPath('start-index')
        self._startServer(
            serviceName='index',
            debugInfo=True,
            executable=executable,
            serviceReadyUrl='http://localhost:%s/als/het/maar/connecten/kan/404/is/prima' % self.gatewayPort, # Ding heeft geen http interface meer... We moeten wat...
            cwd=dirname(abspath(executable)),
            port=self.indexPort,
            luceneserverPort=self.lucenePort,
            gatewayPort=self.gatewayPort,
            stateDir=join(self.integrationTempdir, 'index'),
            quickCommit=True,
            waitForStart=False)

    def startApiServer(self):
        executable = self.binPath('start-api')
        self._startServer(
            serviceName='api',
            executable=executable,
            serviceReadyUrl='http://localhost:%s/info/version' % self.apiPort,
            cwd=dirname(abspath(executable)),
            port=self.apiPort,
            gatewayPort=self.gatewayPort,
            stateDir=join(self.integrationTempdir, 'api'),
            quickCommit=True,
            waitForStart=False)

    def startLuceneServer(self):
        executable = self.binPath('start-lucene-server')
        print 'start-lucene-server', executable
        self._startServer(
            serviceName='lucene',
            executable=executable,
            serviceReadyUrl='http://localhost:%s/info/version' % self.lucenePort,
            port=self.lucenePort,
            stateDir=join(self.integrationTempdir, 'lucene'),
            waitForStart=True,
            core=["narcis"], # core=["oai_dc"],
            env=dict(JAVA_BIN=JAVA_BIN, LANG="en_US.UTF-8"))

    def startSruSlaveServer(self):
        executable = self.binPath('start-sruslave')
        self._startServer(
            serviceName='sruslave',
            executable=executable,
            serviceReadyUrl='http://localhost:%s/info/version' % self.sruslavePort,
            cwd=dirname(abspath(executable)),
            port=self.sruslavePort,
            lucenePort=self.lucenePort,
            stateDir=join(self.integrationTempdir, 'api'),
            waitForStart=False)

    def _createDatabase(self):
        if self.fastMode:
            print "Reusing database in", self.integrationTempdir
            return
        start = time()
        print "Creating database in", self.integrationTempdir
        try:
            for f in sorted(glob(self.testdataDir + '/*.updateRequest')):
            # for f in listdir(self.testdataDir):
                print "Uploading file:", f
                postRequest(self.gatewayPort, '/update', data=open(join(self.testdataDir, f)).read(), parse=False)
            sleepWheel(2)
            print "Finished creating database in %s seconds" % (time() - start)
        except Exception:
            print 'Error received while creating database for', self.stateName
            print_exc()
            sleep(1)
            exit(1)
