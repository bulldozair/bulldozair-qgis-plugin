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
QGisUIManager manage iface interactions with gqis
"""

import os
import re
import json
import operator
from qgis.core.contextmanagers import qgisapp
from qgis.core import QgsProject, edit, QgsField, QgsDataSourceUri, QgsVectorLayer, QgsPluginLayerRegistry, QgsLayerTreeGroup, QgsRasterLayer, QgsLayerTreeLayer, QgsVectorLayerJoinInfo, Qgis, QgsWkbTypes
from qgis.PyQt.QtCore import QCoreApplication, QObject, Qt, QVariant, QSettings
from qgis.PyQt.QtWidgets import QProgressBar, QWidget

_plugin_dir = os.path.dirname(os.path.dirname(__file__))
_qml_dir = os.path.join(_plugin_dir, "ressources", "qml")
_utility_dir = os.path.join(_plugin_dir, "utility")

# with open(os.path.join(os.path.dirname(__file__), "csv_data.json")) as csv_file:
#     __csv_keys__ = json.load(csv_file)


def tr(msg):
    return QCoreApplication.translate("Bulldogis", msg)


class QGisProgressDisplay(object):
    """QProgressBar wrapper to provide minimal interface"""
    def __init__(self):
        self.__widget = QProgressBar()
        self.__widget.setMaximum(100)
        self.__widget.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)

    def widget(self):
        return self.__widget

    def set_ratio(self, ratio):
        self.__widget.setValue(int(ratio*100))

    def __del__(self):
        del self.__widget

class QGisLogger(object):
    def __init__(self, iface):
        self.__iface = iface

    def error(self, title, message):
        self.__iface.messageBar().pushCritical(title, message.replace('\n', ' '))

    def warning(self, title, message):
        self.__iface.messageBar().pushWarning(title, message.replace('\n', ' '))

    def notice(self, title, message):
        # self.__iface.messageBar().pushInfo(title, message.replace('\n', ' '), duration=3)
        pass

    def progress(self, title, message):
        progressMessageBar = self.__iface.messageBar().createMessage(message)
        progress = QGisProgressDisplay()
        progressMessageBar.layout().addWidget(progress.widget())
        self.__iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)
        return progress

    def clear_progress(self):
        self.__iface.messageBar().clearWidgets()


class QGisUIManager(object):
    def __init__(self, iface):
        self.__iface = iface

    def new_project(self):
        self.__iface.newProject()

    def save_project(self, project_filename):
        project = QgsProject.instance()
        project.write(project_filename)

    def open_project(self, project_filename):
        self.__iface.newProject()
        project = QgsProject.instance()
        project.read(project_filename)

        # adds connection to database if not already existing
        bulldo_dbname = project.baseName()
        settings = QSettings()

    def add_vector_layers(self, project_name, model_name, json_file, srid):
        uri = QgsDataSourceUri()
        uri.setConnection(SettingsProperties.get_service(), project_name, '', '')
        uri.setSrid(str(srid))
        __currendir = os.path.dirname(__file__)
        with open(os.path.join(__currendir, json_file)) as j:
            layer_map = json.load(j)
        properties = TablesProperties.get_properties()
        self.__layermap_process(layer_map['objects'], properties, uri, model_name, self.__add_layer_group(model_name, None))
        QgsProject.instance().write(QgsProject.instance().fileName())

    def add_work_layer(self, table_name, layer_name, project_name, column_id, column_geom):
        root = QgsProject.instance().layerTreeRoot()
        if root.findGroup('work') :
            work_group = root.findGroup('work')
        else :
            work_group = root.addGroup('work')

        uri = QgsDataSourceUri()
        uri.setConnection(SettingsProperties.get_service(), project_name, '', '')
        uri.setDataSource('work', table_name, str(column_geom))

        layer = QgsVectorLayer(uri.uri(), tr(layer_name), "postgres")

        QgsProject.instance().addMapLayer(layer, False)
        work_group.addLayer(layer)
        QgsProject.instance().write(QgsProject.instance().fileName())
        return layer.isValid()

    def remove_group_layers(self, group_name, root = QgsProject.instance().layerTreeRoot()):
        group = root.findGroup(group_name)
        if group is not None:
            for child in group.children():
                if isinstance(child, QgsLayerTreeLayer):
                    QgsProject.instance().removeMapLayer(child.layerId())
                else:
                    self.remove_group_layers(child.name(), group)
            root.removeChildNode(group)
        QgsProject.instance().write(QgsProject.instance().fileName())

    def set_model_layers_expanded(self, model_name, expanded=True, checked=True):
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeGroup) and child.name() == model_name:
                child.setExpanded(expanded)
                transparency = 0 if expanded or model_name=='project' else 50
                self.__change_group_transparency(child, transparency)
                self.__change_group_visibility(child, checked)
        QgsProject.instance().write(QgsProject.instance().fileName())

    def __change_group_transparency(self, group, transparency):
        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                if child.layer().type() == 0: #QgsVectorLayer
                    child.layer().setLayerTransparency(int(transparency))
                else:
                    child.layer().renderer().setOpacity(transparency/100.0)
                child.layer().triggerRepaint()
            else:
                self.__change_group_transparency(child, transparency)

    def __change_group_visibility(self, group, visibility):
        for child in group.children():
            if isinstance(child, QgsLayerTreeLayer):
                if child.layer().type() == 0: #QgsVectorLayer
                    self.__iface.legendInterface().setLayerVisible(child.layer(), visibility)
                child.layer().triggerRepaint()
            else:
                self.__change_group_visibility(child, visibility)

    def layer_group_exists(self, group_name='project'):
        tree = QgsProject.instance().layerTreeRoot()
        for leaf in tree.children():
            if isinstance(leaf, QgsLayerTreeGroup) and leaf.name() == group_name:
                return True
        return False

    def __layermap_process(self, items, properties, uri, model_name, current_group):
        for object in items:
            if object['type']=="layer":
                uri.setDataSource(str(model_name), str(object['table']), str(properties[object['table']]['geom']), "", str(properties[object['table']]['key']))
                if properties[object['table']]['type'] == "point":
                    # uri.setWkbType(1)
                    uri.setWkbType(QgsWkbTypes.Point)
                elif properties[object['table']]['type'] in ['segment', 'line']:
                    # uri.setWkbType(2)
                    uri.setWkbType(QgsWkbTypes.LineString)
                elif properties[object['table']]['type'] == 'pointz':
                    # uri.setWkbType(1001)
                    uri.setWkbType(QgsWkbTypes.PointZ)
                elif properties[object['table']]['type'] in ['segmentz', 'linez']:
                    # uri.setWkbType(1002)
                    uri.setWkbType(QgsWkbTypes.LineStringZ)
                elif properties[object['table']]['type'] == "polygon":
                    # uri.setWkbType(3)
                    uri.setWkbType(QgsWkbTypes.Polygon)
                else:
                    raise AttributeError("layer {} has unspecified geometry type".format(str(object['table'])))
                self.__add_layer(uri.uri(), tr(properties[object['table']]['name']), properties[object['table']]['style'],current_group)
            if object['type']=="group":
                self.__layermap_process(object['objects'], properties, uri, model_name, self.__add_layer_group(object['name'], current_group))

    def __add_layer_group(self, group_name, parent):
        if parent==None:
            root = QgsProject.instance().layerTreeRoot()
            group = root.addGroup(tr(group_name))
        else:
            group = QgsLayerTreeGroup(tr(group_name))
            parent.addChildNode(group)
        return group

    def __add_layer(self, path, layer_name, layer_style, group):
        ''' adds a layer to QGIS layer manager. Returns the layer added'''
        if group==None:
            layer = QgsVectorLayer(path, tr(layer_name), "postgres")
            if layer_style is not None:
                layer.loadNamedStyle(os.path.join(_qml_dir, layer_style))
            # if not layer.isValid():
                # raise RuntimeError("invalid postgres layer (uri: {})".format(path))
            QgsProject.instance().addMapLayer(layer)
            return layer
        else:
            layer = QgsVectorLayer(path, tr(layer_name), "postgres")
            if layer_style is not None:
                layer.loadNamedStyle(os.path.join(_qml_dir, layer_style))
            # if not layer.isValid():
                # raise RuntimeError("invalid postgres layer (uri: {})".format(path))
            QgsProject.instance().addMapLayer(layer, False)
            group.addLayer(layer)
            return layer
