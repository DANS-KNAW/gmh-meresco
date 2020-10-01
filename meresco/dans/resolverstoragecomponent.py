# -*- coding: utf-8 -*-
## begin license ##
#
# "Storage" stores data in a reliable, extendable filebased storage
# with great performance.
#
# Copyright (C) 2007-2009 SURF Foundation. http://www.surf.nl
# Copyright (C) 2007 SURFnet. http://www.surfnet.nl
# Copyright (C) 2007-2010 Seek You Too (CQ2) http://www.cq2.nl
# Copyright (C) 2007-2009 Stichting Kennisnet Ict op school. http://www.kennisnetictopschool.nl
# Copyright (C) 2012, 2016-2018 Seecr (Seek You Too B.V.) http://seecr.nl
# Copyright (C) 2012 Stichting Bibliotheek.nl (BNL) http://stichting.bibliotheek.nl
#
# This file is part of "Storage"
#
# "Storage" is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# "Storage" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "Storage"; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
## end license ##

import mysql.connector
import mysql.connector.pooling
import ConfigParser
from os.path import abspath, dirname, join, realpath
from re import compile


urnnbnRegex = compile('^[uU][rR][nN]:[nN][bB][nN]:[nN][lL](:([a-zA-Z]{2}))?:\\d{2}-.+')

class ResolverStorageComponent(object):
    def __init__(self, dbconfig, name=None): # https://pynative.com/python-mysql-tutorial/
        self._dbconfig = self.read_db_config(conffile_path=dbconfig)
        self._name = name
        self._cnxpool = self._create_cnxpool(pool_name="resolver_pool", pool_size=4)
        

    def observable_name(self):
        return self._name

    def addNbnToDB(self, identifier, locations, urnnbn, rgid, isfailover=False):
        """ Add a prioritized list of locations for a pid and repository to storage.
        The locations-list is added in reversed order.
        Therefore the highest priority-location will be inserted last and will resolve first.

        :param identifier: meresco uploadid of this record
        :param locations: prioritized list of locations
        :param urnnbn: urn:nbn persistent identifier
        :param rgid: meresco repository group identifier
        :param isfailover: if True, the locations given are failover locations.
        :return: void
        """
        rgid = rgid.lower()
        urnnbn = urnnbn.lower()

        if not urnnbnRegex.match(urnnbn): # DIDL normalisation rejects records with invalid urn:nbn identifiers. So this check is overhead, for this situation.
            return

        try: #TODO: Move all into one transaction.
            registrant_id = self._selectOrInsertRegistrantId_pl(rgid)
            # print "registrant_id:", registrant_id
            identifier_id = self._selectOrInsertIdentifierId_pl(registrant_id, urnnbn)
            # print "identifier_id:", identifier_id
            # Delete all identifier/location pairs from identifier_location table linked to this registrant and identifier...
            self._deletePairsByRegId_pl(registrant_id, identifier_id)
            location_ids = self._selectOrInsertLocationsId_pl(registrant_id, locations)
            # print "location_ids:", location_ids
            self._insertIdentifierLocations_pl(identifier_id, location_ids, isfailover)

        except mysql.connector.Error as e:
            print("Error from SQL-db: ", e)

        return


    # def _getDBLocationsByNBN_pl(self, nbn_id):
    #     try:
    #         conn = self._cnxpool.get_connection()
    #         cursor = conn.cursor()
    #         sql = """SELECT L.location_url, IL.isFailover
    #                 FROM identifier I 
    #                 JOIN identifier_location IL ON I.identifier_id = IL.identifier_id
    #                 JOIN location L ON L.location_id = IL.location_id
    #                 WHERE I.identifier_value= '{}'
    #                 ORDER BY IL.isFailover, IL.last_modified DESC;""".format(nbn_id)
    #         cursor.execute(sql)
    #         res = cursor.fetchall()
    #         self.close(conn, cursor)
    #         return res
    #     except mysql.connector.Error as err:
    #         print "Error while execute'ing SQL-query: {}: {}".format(sql, err)


    def _insertIdentifierLocations_pl(self, identifier_id, location_ids, isFailover=False):
        try:
            conn = self._cnxpool.get_connection()
            cursor = conn.cursor()

            for location_id in location_ids: #loc/id pair may already exist (uploaded by another repo)...
                sql = "SELECT * FROM identifier_location WHERE location_id={} AND identifier_id={}".format(location_id, identifier_id)
                cursor.execute(sql)
                res = cursor.fetchall()
                if len(res) == 0:
                    sql = "INSERT INTO identifier_location (location_id, identifier_id, isFailover) VALUES ('{}','{}','{}')".format(location_id, identifier_id, 1 if isFailover else 0 )
                    cursor.execute(sql)
                    conn.commit()
            self.close(conn, cursor)
        except mysql.connector.Error as err:
            print "Error while execute'ing SQL-query: {}".format(err)

    def _deletePairsByRegId_pl(self, registrant_id, identifier_id):
        try:
            conn = self._cnxpool.get_connection()
            cursor = conn.cursor()
            sql = """DELETE identifier_location
                FROM identifier_location
                INNER JOIN location_registrant ON identifier_location.location_id = location_registrant.location_id
                WHERE location_registrant.registrant_id = '{}' AND identifier_location.identifier_id = '{}'""".format(registrant_id, identifier_id)
            # print sql
            cursor.execute(sql)
            conn.commit()
            self.close(conn, cursor)
        except mysql.connector.Error as err:
            print "Error while execute'ing SQL-query: {}".format(err)


    def _selectOrInsertLocationsId_pl(self, registrant_id, locations):
        """
        The locations-list is added in reversed order. Therefore the highest priority-location will be inserted last and will resolve first.
        """
        location_ids=[]
        try:
            conn = self._cnxpool.get_connection()
            cursor = conn.cursor()

            for location_url in reversed(locations):
                sql = """SELECT location.location_id
                         FROM location
                         INNER JOIN location_registrant ON location.location_id = location_registrant.location_id
                         WHERE location_registrant.registrant_id = '{}' AND location.location_url = '{}'""".format(registrant_id, location_url)
                cursor.execute(sql)
                res = cursor.fetchall()
                if len(res) > 0:
                    location_ids.append(res[0][0])
                else:  # location_id not available for this repo. Insert it (if not exists) and return the location_id.
                    sql = """SELECT location.location_id
                             FROM location
                             WHERE location.location_url = '{}'""".format(location_url)
                    cursor.execute(sql)
                    res = cursor.fetchall()
                    if len(res) > 0:
                        location_id = res[0][0]
                    else:
                        sql = "INSERT INTO location (location_url) VALUES ('%s')" % location_url
                        cursor.execute(sql)
                        location_id = cursor.lastrowid
                    # Insert location_id into location_registrant table, to register this id with the registrant:
                    sql = "INSERT INTO location_registrant (location_id, registrant_id) VALUES ('{}', '{}')".format(location_id, registrant_id)
                    cursor.execute(sql)
                    conn.commit()
                    location_ids.append(location_id)
            self.close(conn, cursor)
            return location_ids
        except mysql.connector.Error as err:
            print "Error while execute'ing SQL-query: {}".format(err)
        return location_ids


    def _selectOrInsertIdentifierId_pl(self, registrant_id, identifier_value):
        try:
            conn = self._cnxpool.get_connection()
            cursor = conn.cursor()
            sql = """SELECT identifier.identifier_id
                     FROM identifier
                     INNER JOIN identifier_registrant ON identifier.identifier_id = identifier_registrant.identifier_id
                     WHERE identifier_registrant.registrant_id = '{}' AND identifier.identifier_value = '{}'""".format(registrant_id, identifier_value)
            cursor.execute(sql)
            res = cursor.fetchall()
            if len(res) > 0:
                identifier_id = res[0][0]
            else:  # identifier_id not available for this repo. Insert it (if not exists) and return the identifier_id.
                sql = """SELECT identifier.identifier_id
                         FROM identifier
                         WHERE identifier.identifier_value = '{}'""".format(identifier_value)
                cursor.execute(sql)
                res = cursor.fetchall()
                if len(res) > 0:
                    identifier_id = res[0][0]
                else:
                    sql = "INSERT INTO identifier (identifier_value) VALUES ('%s')" % identifier_value
                    cursor.execute(sql)
                    identifier_id = cursor.lastrowid
                # Insert identifier_id into identifier_registrant table, to register this id with the registrant:
                sql = "INSERT INTO identifier_registrant (identifier_id, registrant_id) VALUES ('{}', '{}')".format(identifier_id, registrant_id)
                cursor.execute(sql)
                conn.commit()
            self.close(conn, cursor)
            return identifier_id
        except mysql.connector.Error as err:
            print "Error while execute'ing SQL-query: {}".format(err)


    def _selectOrInsertRegistrantId_pl(self, rgid):
        try:
            conn = self._cnxpool.get_connection()
            # print conn.get_server_info()
            cursor = conn.cursor()
            sql = "SELECT * FROM registrant WHERE registrant_groupid = '%s'" % rgid
            cursor.execute(sql)
            res = cursor.fetchall()
            if len(res) > 0 :
                registrant_id = res[0][0]
            else:  # registrant_id not available from DB. Insert it and return the new id.
                sql = "INSERT INTO registrant (registrant_groupid) VALUES ('%s')" % rgid
                cursor.execute(sql)
                registrant_id = cursor.lastrowid
                conn.commit()
            self.close(conn, cursor)
            return registrant_id
        except mysql.connector.Error as err:
            print "Error while execute'ing SQL-query: {}".format(err)


    def read_db_config(self, conffile_path, section='mysql'): #TODO: Even importeren ergens anders vandaan. Dubbele code...
        """ Read database configuration file and return a dictionary object
        :param filename: name of the configuration file
        :param section: section of database configuration
        :return: a dictionary of database parameters
        """
        # create parser and read ini configuration file
        parser = ConfigParser.ConfigParser()
        parser.read(conffile_path)

        # get section, default to mysql
        db = {}
        if parser.has_section(section):
            items = parser.items(section)
            for item in items:
                db[item[0]] = item[1]
        else:
            raise Exception('{0} not found in the {1} file'.format(section, conffile_path))
        print "DB-configfile read from: {0}".format(conffile_path, )
        return db

    def _create_cnxpool(self, pool_name="mypool", pool_size=5):
        """
        Create a connection pool, after created, the request of connecting
        MySQL could get a connection from this pool instead of request to
        create a connection.
        :param pool_name: the name of pool, default is "mypool"
        :param pool_size: the size of pool, default is 3
        :return: connection pool
        """
        try:
            pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                pool_reset_session=True,
                **self._dbconfig)
            print "Created ConnectionPool: Name=", pool.pool_name, ", Poolsize=", pool.pool_size
            return pool
        except mysql.connector.Error as err:
            print "Error while creating MySQL Connection pool : {}".format(err)

        # To close ALL connections in the pool: https://github.com/mysql/mysql-connector-python/blob/master/lib/mysql/connector/pooling.py#L335
        # pool._remove_connections()

    def close(self, conn, cursor):
        """
        A method used to close connection of mysql.
        :param conn:
        :param cursor:
        :return:
        """
        cursor.close()
        conn.close()

