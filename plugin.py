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
QGIS plugin
"""

import os
import sqlite3
import traceback
import json
import requests
import re
import sys
import subprocess
import webbrowser
from datetime import datetime
from functools import partial
from qgis.core import QgsProject, QgsPluginLayerRegistry, QgsCoordinateReferenceSystem, QgsSettings, QgsApplication, Qgis, QgsProviderRegistry, QgsProviderMetadata, QgsVectorLayer
from qgis.PyQt.QtCore import QTranslator, QCoreApplication, QObject, Qt, QSize
from qgis.PyQt.QtWidgets import QToolBar, QMenu, QAction, QWidget, QComboBox, QToolButton, QFileDialog, QGroupBox, QInputDialog, QLabel, QDockWidget, QMessageBox, QApplication, QPushButton, QVBoxLayout, QScrollArea
from qgis.PyQt.QtGui import QIcon, QPixmap
from .utility.qgis_utilities import QGisUIManager, QGisLogger
from .utility.log import LogManager
from .gui import new_project_dialog as npdialog, manage_project_dialog as mpd 

def tr(msg):
    return QCoreApplication.translate("Bulldogis", msg)

_plugin_dir = os.path.dirname(__file__)
_bulldo_dir = os.path.join(os.path.expanduser('~'), ".bulldo")
# _layer_icons_dir = os.path.join(_plugin_dir, "ressources", "layer_icons")
# _log_file = os.path.join(_bulldo_dir, 'bulldo.log')
# _desktop_dir = os.path.join(os.path.expanduser('~'), "Desktop")


class BulldoGis(QObject):
    '''QGIS Plugin Implementation.'''

    def __init__(self, iface):
        '''Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        '''
        QObject.__init__(self)
        self.__iface = iface

        # initialize locale
        locale = QgsSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            _plugin_dir,
            'i18n',
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.__translator = QTranslator()
            self.__translator.load(locale_path)
            QCoreApplication.installTranslator(self.__translator)

        self.__project_menu = None
        self.__currentproject = None
        self.__action_current = None

        self.__ui_manager = QGisUIManager(self.__iface)
        self.__log_manager = LogManager(QGisLogger(self.__iface), tr("BulldoGis"))

        try:
            self.__conn = sqlite3.connect(os.path.join(_bulldo_dir,'sqllite_bulldo.db'))
            self.__cur = self.__conn.cursor()
        except Exception as error:
            self.log.error(tr('Database ') + os.path.join(_bulldo_dir,'sqllite_bulldo.db') + tr(' not found.'))
            raise


        # if os.name == 'nt':
        #     deploy_dependencies(_plugin_dir, self.__log_manager)
        QgsProject.instance().readProject.connect(self.project_loaded)

    @property
    def project(self):
        """return current project instance"""
        return self.__currentproject

    def initGui(self):
        '''create the menu entries and toolbar icons inside the QGIS GUI'''
        self.__iface.mainWindow().menuBar().addMenu(self.project_menu())
        self.__currentproject = None

    def project_loaded(self, dom):
        project_path = QgsProject.instance().readPath("./")
        project_name = project_path.split("/")[-1]

    def unload(self):
        '''Removes the plugin menu item and icon from QGIS GUI.'''
        self.__project_menu.setParent(None)
        self.__project_menu = None
        self.__iface.newProject()

    def project_menu(self):
        '''returns the project menu, creates it if needed'''
        if not self.__project_menu:
            self.__project_menu = QMenu(tr("&BulldoGis"))
            self.__project_menu.setIcon(QIcon(os.path.join(_plugin_dir, 'ressources', 'images', 'logo.png')))
            self.__project_menu.addAction(tr("&New project")).triggered.connect(self.__project_new)
            self.__project_menu.addAction(tr("&Remove project")).triggered.connect(self.__project_remove)
            self.__project_menu.addAction(tr("&Manage projects")).triggered.connect(self.__project_manage)
            self.__project_menu.addSeparator()

            self.__project_menu.addAction(tr("Reload project &layers")).triggered.connect(self.__project_layers_load)
            self.__project_menu.addAction(tr("&Download project layers")).triggered.connect(self.__project_download)
            self.__project_menu.addSeparator()

            self.__project_menu.addAction(tr("About Bulldozair")).triggered.connect(self.__about)

        return self.__project_menu

    def __project_new(self):
        ''' take api token and password to create a bulldozair project '''
        new_project_dialog = npdialog.NewProjectDialog(self.__iface.mainWindow())
        if new_project_dialog.exec_():
            name, url = new_project_dialog.get_credentials()

        self.__cur.execute('''INSERT INTO PROJECT(name, url) 
        values ('{name}', '{url}')'''.format(name=name, url=url))

        self.__conn.commit()
        return

    def __project_remove(self):
        ''' remove a project '''
        list_projects = [item for (item,) in self.__cur.execute(''' select name from project''')]

        select_project = mpd.ManageProjectDialog(self.__iface.mainWindow(), projects=list_projects)
        if select_project.exec_():
            self.__cur.execute(''' delete from project where name ='{name}' '''.format(name=select_project.get_project()))

        self.__conn.commit()
        return

    
    def __project_manage(self):
        ''' show all bulldozair project and change current '''
        if self.__action_current is not None:
                self.__project_menu.removeAction(self.__action_current)
                self.__action_current = None

        list_projects = [item for (item,) in self.__cur.execute(''' select name from project''')]
        # print(list_projects)

        select_project = mpd.ManageProjectDialog(self.__iface.mainWindow(), projects=list_projects)
        if select_project.exec_():
            self.__currentproject = select_project.get_project()
            if self.__currentproject is not None:
                self.__action_current = QAction("Current project : " + self.__currentproject, self.__project_menu)
                self.__project_menu.addAction(self.__action_current)

        return

    def __project_download(self):
        ''' download_gpkg '''
        res = self.__cur.execute(''' select name , url from project where name ='{name}' '''.format(name=self.__currentproject)).fetchone()
        (name, url) = res

        r = requests.get(url, allow_redirects=True)

        open(os.path.join(_bulldo_dir, name+'.gpkg'), 'wb').write(r.content)

    def __project_layers_load(self):
        ''' load all buldozair layers in a Qtree '''

        print(self.__currentproject)

        if self.__currentproject is not None:
            # To do load layers
            res = self.__cur.execute(''' select name , url from project where name ='{name}' '''.format(name=self.__currentproject)).fetchone()
            (name, url) = res

            if name is not None:
                # base_url = 'https://backend-prod2.bulldozair.com/v1/enterprise_api/projects'

                data_store = [
                    ['pictures'],
                    ['forms'],
                    ['tasks']
                ]

                for d in data_store :
                    self.add_layer(url, d[0])

        else:
            print("No current project")

        return

    def add_layer(self, uri, layer_name):
        root = QgsProject.instance().layerTreeRoot()
        if root.findGroup('bulldo') :
            bulldo_group = root.findGroup('bulldo')
        else :
            bulldo_group = root.addGroup('bulldo')

        layer = QgsVectorLayer(uri+'|layername='+layer_name, self.__currentproject +'-'+tr(layer_name), "ogr")

        if layer_name == 'pictures':
            layer.setMapTipTemplate('<img src="[% picture_file_url %]" width=300 height=300 />')

        QgsProject.instance().addMapLayer(layer, False)
        bulldo_group.addLayer(layer)
        QgsProject.instance().write(QgsProject.instance().fileName())
        return layer.isValid()

    def __about(self):
        # build_info = get_build().split('\n')
        # version =  build_info[1].split(':')[1]
        # date_ = datetime.fromtimestamp(os.stat(build_file).st_ctime).strftime("%Y-%m-%d")

        about_pic = QPixmap(os.path.join(_plugin_dir, 'ressources', 'images', 'logo.png')).scaledToHeight(32, Qt.SmoothTransformation)

        about_text = f"<b>BulldoGis version </b><br><br>"
        about_text += "<br>Bulldozair : https://www.bulldozair.com<br><b>"
        # about_file = os.path.join(_plugin_dir, 'license_short.txt')
        # with open(about_file, 'r') as f:
        #     about_text += f.read()
        

        about_box = QMessageBox()
        about_box.setWindowTitle(tr('About Bulldozair'))
        about_box.setIconPixmap(about_pic)
        about_box.setTextFormat(Qt.RichText)
        about_box.setText(about_text)
        about_box.exec_()