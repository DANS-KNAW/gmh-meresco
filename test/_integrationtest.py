## begin license ##
#
# "Meresco Examples" is a project demonstrating some of the
# features of various components of the "Meresco Suite".
# Also see http://meresco.org.
#
# Copyright (C) 2012-2016 Seecr (Seek You Too B.V.) http://seecr.nl
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

from os import getuid
import sys
assert getuid() != 0, "Do not run tests as 'root'"


from seecrdeps import includeParentAndDeps
includeParentAndDeps(__file__, scanForDeps=True)

from seecr.test.testrunner import TestRunner
from _integration import GmhTestIntegrationState

if __name__ == '__main__': #TODO: arg[0] fastMode uitlezen. 
    runner = TestRunner()
    # Setting fastmode to True, will SKIP the upload part, and reuse existing database/store for the integration tests.
    runner.fastMode = False
    print "FASTMODE:", runner.fastMode

    GmhTestIntegrationState(
        "brigmh",
        tests=[
            '_integration.gatewaytest.GatewayTest',
            # '_integration.apitest.ApiTest',
            # '_integration.sruslavetest.SruSlaveTest',
        ],
        fastMode=runner.fastMode
        ).addToTestRunner(runner)
    runner.run()

