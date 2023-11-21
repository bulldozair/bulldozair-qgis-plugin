# coding=utf-8

################################################################################################
##                                                                                            ##
##     This file is part of Bulldogis, a QGIS plugin for BulldozAIR                           ##
##     (see <https://www.bulldozair.com//>).                                                  ##
##                                                                                            ##
##     Copyright (c) 2023 by BulldozAIR.                                                      ##
##                                                                                            ##
##     Contact: <contact@bulldozair.com>                                                      ##
##                                                                                            ##
##     You can use this program under the terms of the MIT Expat License                      ##
##     License as published by the Open Source Initiative.                                    ##
##                                                                                            ##
##                                                                                            ##
##     You should have received a copy of the MIT License                                     ##
##     along with this program. If not, see <https://opensource.org/license/mit/>.            ##
##                                                                                            ##
################################################################################################

"""
 This script initializes the plugin, making it known to QGIS.
"""
import sqlite3
import os
import json
import subprocess
import requests
import xml.etree.ElementTree as ET
from distutils.version import StrictVersion
from configparser import ConfigParser
from qgis.utils import pluginMetadata
from qgis.core import Qgis
from qgis.PyQt.QtWidgets import QPushButton

_bulldo_dir = os.path.join(os.path.expanduser('~'), ".bulldo")

def open_plugin_manager():
    import pyplugin_installer
    pyplugin_installer.instance().showPluginManagerWhenReady()

def classFactory(iface):

    # create bulldo directory
    if not os.path.isdir(_bulldo_dir):
        os.makedirs(_bulldo_dir)

    # default sqlite base for plugin
    sqliteConnection = sqlite3.connect(os.path.join(_bulldo_dir,'sqllite_bulldo.db'))
    cursor = sqliteConnection.cursor()


    sqliteConnection = sqlite3.connect(os.path.join(_bulldo_dir,'sqllite_bulldo.db'))
    sqlite_create_table_query = '''CREATE TABLE IF NOT EXISTS project (
                                id INTEGER PRIMARY KEY,
                                name TEXT NOT NULL,
                                url text NOT NULL UNIQUE
                                );'''

    cursor.execute(sqlite_create_table_query)
    sqliteConnection.commit()

    from .plugin import BulldoGis
    return BulldoGis(iface)
