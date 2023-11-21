# coding=utf-8

################################################################################################
##                                                                                            ##
##     This file is part of HYDRA, a QGIS plugin for hydraulics                               ##
##     (see <http://hydra-software.net/>).                                                    ##
##                                                                                            ##
##     Copyright (c) 2017 by HYDRA-SOFTWARE, which is a commercial brand                      ##
##     of Setec Hydratec, Paris.                                                              ##
##                                                                                            ##
##     Contact: <contact@hydra-software.net>                                                  ##
##                                                                                            ##
##     You can use this program under the terms of the GNU General Public                     ##
##     License as published by the Free Software Foundation, version 3 of                     ##
##     the License.                                                                           ##
##                                                                                            ##
##     You should have received a copy of the GNU General Public License                      ##
##     along with this program. If not, see <http://www.gnu.org/licenses/>.                   ##
##                                                                                            ##
################################################################################################

import os
from qgis.PyQt import uic
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtWidgets import QDialog, QMessageBox, QFileDialog, QDialogButtonBox

_bulldo_dir = os.path.join(os.path.expanduser('~'), ".bulldo")

def tr(msg):
    return QCoreApplication.translate("Bulldo", msg)

class NewProjectDialog(QDialog):
    def __init__(self, parent=None, project_name='', project_id='', api_key=''):
        QDialog.__init__(self, parent)
        current_dir = os.path.dirname(__file__)
        uic.loadUi(os.path.join(current_dir, "new_project_dialog.ui"), self)


    def get_credentials(self):
        return self.project_name.text(), self.url.text()