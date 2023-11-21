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

import os
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QFileDialog, QDialogButtonBox

_bulldo_dir = os.path.join(os.path.expanduser('~'), ".bulldo")

def tr(msg):
    return QCoreApplication.translate("Bulldo", msg)

class ManageProjectDialog(QDialog):
    def __init__(self, parent=None, projects=[]):
        QDialog.__init__(self, parent)
        current_dir = os.path.dirname(__file__)
        uic.loadUi(os.path.join(current_dir, "manage_project_dialog.ui"), self)

        # print(projects)

        self.combo_projects.addItems(projects)

        self.combo_projects.currentTextChanged.connect(self.project_changed)

    def get_project(self):
        return str(self.combo_projects.currentText())
        
    def project_changed(self):
        self.current_project.setText(str(self.combo_projects.currentText()))