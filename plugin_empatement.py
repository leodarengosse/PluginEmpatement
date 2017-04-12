# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PluginEmpatement
                                 A QGIS plugin
 Ce plugin cherche les empâtements sur des polylignes
                              -------------------
        begin                : 2017-03-14
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Léo Darengosse
        email                : leo.darengosse@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from plugin_empatement_dialog import PluginEmpatementDialog
import os.path

import sys
from PyQt4.QtCore import *
from PyQt4.QtNetwork import QHttp, QNetworkProxy
from owslib.wms import WebMapService
from owslib.wmts import WebMapTileService
from PyQt4.QtGui import QInputDialog
import unicodedata
from PyQt4 import QtCore, QtGui
from qgis.core import QgsRasterLayer,QgsMapLayerRegistry,QgsVectorLayer,QgsCoordinateReferenceSystem
from PyQt4.QtGui import QMessageBox
from qgis.utils import iface
# Import the code for the DockWidget
import os.path
from qgis.core import *
from PyQt4.QtCore import *
from qgis.core import QgsVectorLayer, QgsField, QgsMapLayerRegistry, QgsFeature, QgsGeometry, QgsPoint, QgsCoordinateReferenceSystem, QgsCoordinateTransform
import os
from qgis.core import *
import processing, os
from PyQt4.QtCore import *
from math import *
import time
from PyQt4.QtGui import QApplication, QProgressBar, QWidget
from qgis.gui import QgsMessageBar


class PluginEmpatement:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PluginEmpatement_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = PluginEmpatementDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Détection des empâtements')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'PluginEmpatement')
        self.toolbar.setObjectName(u'PluginEmpatement')

        self.dlg.pushButton_importer.clicked.connect(self.open_file)
        self.dlg.pushButton_exporter.clicked.connect(self.select_output_folder)

        self.dlg.button_box.accepted.connect(self.run_recherche_empatement)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PluginEmpatement', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        #self.dlg = PluginEmpatementDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/PluginEmpatement/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Recherche des empâtements'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Détection des empâtements'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.comboBox_layers.clear()
        self.layers_canevas = self.iface.legendInterface().layers()
        layer_list = []
        for layer in self.layers_canevas:
            layer_list.append(layer.name())
        self.dlg.comboBox_layers.addItems(layer_list)
        # Remise à zéro du nom de fichier selectionné (s'il y en a déjà un)
        # self.dlg.lineEdit_fichier_import.clear()
        # self.dlg.lineEdit_chemin_export.clear()
        # Lien entre le click sur le pushButton et la fonction open_file

        self.dlg.lineEdit_fichier_import.clear()
        self.dlg.lineEdit_chemin_export.clear()
        #self.dlg.pushButton_importer.clicked.connect(self.open_file)
        #self.dlg.pushButton_exporter.clicked.connect(self.select_output_folder)


        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def open_file(self):
        """ Fonction qui permet de choisir le fichier .shp à ouvrir"""
        self.filename = QtGui.QFileDialog.getOpenFileName(self.dlg, 'Open File', '', '*.shp')
        self.dlg.lineEdit_fichier_import.setText(self.filename)
        #my_dir = QtGui.QFileDialog.getExistingDirectory(self,"Open a folder","/home/eva/",QtGui.QFileDialog.ShowDirsOnly)

    def select_output_folder(self):
        self.cheminEnregistrement = QtGui.QFileDialog.getExistingDirectory(self.dlg, "Select output folder ", '')
        self.dlg.lineEdit_chemin_export.setText(self.cheminEnregistrement)


    def run_recherche_empatement(self):

            self.chemin_fichier_import = self.dlg.lineEdit_fichier_import.text()
            self.chemin_export = self.dlg.lineEdit_chemin_export.text()
            self.buffer_distance = int(self.dlg.spinBox_taille_buffer.text())
            self.nb_min_empatement = int(self.dlg.spinBox_nb_min_empatement.text())
            self.coef_empatement = float(str(self.dlg.doubleSpinBox_coef_empatement.text()).replace(',','.')) #conversion en float

            if (self.chemin_export):
                if(self.chemin_fichier_import) :

                    layer = self.chemin_fichier_import.split('/')
                    n = len(layer)
                    layername = layer[n-1].split('.')

                    # On ajoute la couche sélectionnée au projet
                    self.layer_traj = QgsVectorLayer(self.chemin_fichier_import , str(layername[0]), "ogr")
                    QgsMapLayerRegistry.instance().addMapLayers([self.layer_traj])
                    self.recherche_empatement(self.layer_traj,self.chemin_export,self.buffer_distance, self.coef_empatement, self.nb_min_empatement)

                else:

                    selectedLayerIndex = self.dlg.comboBox_layers.currentIndex()
                    selectedLayer = self.layers_canevas[selectedLayerIndex]
                    self.layer_traj = selectedLayer
                    self.recherche_empatement(self.layer_traj,self.chemin_export,self.buffer_distance, self.coef_empatement, self.nb_min_empatement)


            else :

                QMessageBox.information(None, "Avertissement","Veuillez choisir un dossier de destination")





    def recherche_empatement(self, layer_traj,cheminEnregistrement,buffer_distance, coef_empatement, nb_min_empatement):

        print('Extraction des noeuds des trajectoires...')

        traj_noeuds = processing.runalg('qgis:extractnodes', layer_traj, None)['OUTPUT']
        traj_noeuds = QgsVectorLayer(traj_noeuds,"traj_noeuds", "ogr")


        def dist (x1,y1,x2,y2):
            return sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1))


        def calcul_angle_consecutifs(layer_noeuds, layer_traj):

            progressMessageBar = iface.messageBar().createMessage("Calcul des angles consecutifs des trajectoires...")
            progress = QProgressBar()
            progress.setMaximum(100)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            iface.messageBar().pushWidget(progressMessageBar, iface.messageBar().INFO)

            layer_noeuds.selectAll()

            #Count all selected feature
            count = layer_noeuds.selectedFeatureCount()

            print('Calcul des angles consecutifs des trajectoires...')

            list_noeuds = list()
            list_angle = list()

            for noeud in layer_noeuds.getFeatures():
        ##        print str(noeud.geometry().asPoint().x()) + "," + str(noeud.geometry().asPoint().y())
                list_noeuds.append(noeud)

            nb_virages = 0

            for i in range(0,len(list_noeuds)):

                percent = (i/float(count)) * 100
                progress.setValue(percent) #pour faire avancer la barre de progression

                request = QgsFeatureRequest().setFilterExpression( '"id" = \'%s\'' % list_noeuds[i]['id'] )

                traj_select = layer_traj.getFeatures(request).next()
                debut_traj_x = traj_select.geometry().asPolyline()[0].x()
                fin_traj_x = traj_select.geometry().asPolyline()[-1].x()

                noeud_x = list_noeuds[i].geometry().asPoint().x()
                noeud_y = list_noeuds[i].geometry().asPoint().y()

                if (noeud_x != debut_traj_x and noeud_x != fin_traj_x): #si on se situe a une extremite de la trajectoire on ne calcule pas d'angle

                    noeud_avant_x = list_noeuds[i-1].geometry().asPoint().x()
                    noeud_avant_y = list_noeuds[i-1].geometry().asPoint().y()

                    noeud_apres_x = list_noeuds[i+1].geometry().asPoint().x()
                    noeud_apres_y = list_noeuds[i+1].geometry().asPoint().y()

                    sin = ((noeud_apres_x-noeud_x)*(noeud_y-noeud_avant_y)-(noeud_x-noeud_avant_x)*(noeud_apres_y-noeud_y))/(dist(noeud_x,noeud_y,noeud_avant_x,noeud_avant_y)*dist(noeud_apres_x,noeud_apres_y,noeud_x,noeud_y))
        ##            print sin
                    if round(sin,1) == 1: #il y a une erreur lorsque le sinus vaut 1.0 pour une raison inconnue
                        angle = 1.57079633
                    else :
                        angle = asin(sin)
        ##            print angle
                    list_angle.append(round(angle,8))

        ##        angle = atan(oppose/adjacent)*180/3.14159
        ##        if angle > 180:
        ##            angle = 360 - angle
                    nb_virages +=1
                else:
                    angle = 0 #angle nul aux extremites
        ##            print angle
                    list_angle.append(round(angle,8))

                    # print angle*180/3.14159
        ##    print nb_virages

            #ajout d'un champ angle_rad a notre table de noeuds en entree
            layer_noeuds.startEditing()
            idx_angle_noeuds = layer_noeuds.fieldNameIndex("angle_rad")

            if (idx_angle_noeuds == -1): #si le champs n'existe pas
                layer_noeuds.dataProvider().addAttributes( [QgsField("angle_rad", QVariant.Double ,'double', 20, 8)])
                layer_noeuds.updateFields()
                idx_angle_noeuds = layer_noeuds.fieldNameIndex("angle_rad")

            # on remplit la table avec les angles calcules
            i = 0
            for feat_noeuds in layer_noeuds.getFeatures():
        ##        print i
        ##        print idx_angle_noeuds
        ##        print list_angle[i]
        ##
                layer_noeuds.changeAttributeValue(feat_noeuds.id(), idx_angle_noeuds, list_angle[i])
                i+=1

            #application des modifications sur la couche
            layer_noeuds.updateExtents()
            layer_noeuds.commitChanges()

            layer_noeuds.removeSelection()
            iface.messageBar().clearWidgets()


        calcul_angle_consecutifs(traj_noeuds, layer_traj)


        print('Bufferisation...')

        buffer = processing.runalg('qgis:fixeddistancebuffer', layer_traj, buffer_distance, 1, False, None)['OUTPUT']
        buffer = QgsVectorLayer(buffer,"buffer", "ogr")

        print('Extraction des contours du buffer...')
        buffer_ligne = processing.runalg("qgis:polygonstolines",buffer,None)['OUTPUT']
        buffer_ligne = QgsVectorLayer(buffer_ligne,"buffer_ligne", "ogr")

        print('Extraction des lignes (Offset)...')
        buffer_line_explode = processing.runalg('qgis:explodelines', buffer_ligne, None)['OUTPUT']
        line_offset = QgsVectorLayer(buffer_line_explode,"line_offset", "ogr")

        print('Extraction des noeuds (Offset)...')
        line_offset_noeuds = processing.runalg('qgis:extractnodes', line_offset, None)['OUTPUT']

        print('Suppression des doublons (noeuds Offset)...')
        line_offset_noeuds = processing.runalg('qgis:deleteduplicategeometries', line_offset_noeuds, None)['OUTPUT']
        line_offset_noeuds = QgsVectorLayer(line_offset_noeuds,"line_offset_noeuds", "ogr")
        # QgsMapLayerRegistry.instance().addMapLayers([line_offset_noeuds])
        # QgsMapLayerRegistry.instance().addMapLayers([buffer_ligne])

        def calcul_angle_consecutifs_offset(layer_noeuds, layer_traj):

            progressMessageBar = iface.messageBar().createMessage("Calcul des angles consecutifs (Offset)...")
            progress = QProgressBar()
            progress.setMaximum(100)
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            iface.messageBar().pushWidget(progressMessageBar, iface.messageBar().INFO)

            layer_noeuds.selectAll()

            #Count all selected feature
            count = layer_noeuds.selectedFeatureCount()

            print('Calcul des angles consecutifs (Offset)...')

            list_noeuds = list()
            list_angle = list()

            for noeud in layer_noeuds.getFeatures():
        ##        print str(noeud.geometry().asPoint().x()) + "," + str(noeud.geometry().asPoint().y())
                list_noeuds.append(noeud)

            nb_virages = 0

            for i in range(0,len(list_noeuds)):

                request = QgsFeatureRequest().setFilterExpression( '"id" = \'%s\'' % list_noeuds[i]['id'] ) #pour travailler que sur le meme offset
                print list_noeuds[i]['id']
                debut_traj_x = 0

                for traj in layer_traj.getFeatures(request): #recherche du premier et dernier point de la polyligne (c'est inverse je sais pas pourquoi)

                    debut_traj_x = traj.geometry().asPolyline()[-1].x()
                    debut_traj_y = traj.geometry().asPolyline()[-1].y()
                    fin_traj_x = traj.geometry().asPolyline()[0].x()
                    fin_traj_y = traj.geometry().asPolyline()[0].y()

                noeud_x = list_noeuds[i].geometry().asPoint().x() #noeud sur lequel on se place a chaque iteration
                noeud_y = list_noeuds[i].geometry().asPoint().y()

                print list_noeuds[i]['id']
                print("Points : " + str(i))
                print("debut_traj_x : " + str(debut_traj_x))
                print("fin_traj_x : " + str(fin_traj_x))
                print("noeud_x : " + str(noeud_x))
                print("noeud_y : " + str(noeud_y))


                if(noeud_x == debut_traj_x): #si on se situe au premier point de la polyligne on calcule son angle avec le dernier (qui devient le noeuds d'avant)

                    noeud_avant_x = fin_traj_x
                    noeud_avant_y = fin_traj_y

                    noeud_apres_x = list_noeuds[i+1].geometry().asPoint().x()
                    noeud_apres_y = list_noeuds[i+1].geometry().asPoint().y()

                    sin = ((noeud_apres_x-noeud_x)*(noeud_y-noeud_avant_y)-(noeud_x-noeud_avant_x)*(noeud_apres_y-noeud_y))/(dist(noeud_x,noeud_y,noeud_avant_x,noeud_avant_y)*dist(noeud_apres_x,noeud_apres_y,noeud_x,noeud_y))

                    if round(sin,1) == 1: #il y a une erreur lorsque le sinus vaut 1.0 pour une raison inconnue
                        angle = 1.57079633
                    else :
                        angle = asin(sin)

        ##            print("Angle : " + str(angle*180/3.14159))
                    list_angle.append(round(angle,8))

                    nb_virages +=1

        ##            layer_traj.changeAttributeValue(i, idx_angle, angle)
        ##            layer_noeuds.changeAttributeValue(i, idx_angle, angle)

                elif(noeud_x == fin_traj_x): #si on se situe au dernier point de la polyligne on calcule son angle avec le premier (qui devient le noeuds d'apres)
                    noeud_avant_x = list_noeuds[i-1].geometry().asPoint().x()
                    noeud_avant_y = list_noeuds[i-1].geometry().asPoint().y()

                    noeud_apres_x = debut_traj_x
                    noeud_apres_y = debut_traj_y

                    sin = ((noeud_apres_x-noeud_x)*(noeud_y-noeud_avant_y)-(noeud_x-noeud_avant_x)*(noeud_apres_y-noeud_y))/(dist(noeud_x,noeud_y,noeud_avant_x,noeud_avant_y)*dist(noeud_apres_x,noeud_apres_y,noeud_x,noeud_y))

                    if round(sin,1) == 1: #il y a une erreur lorsque le sinus vaut 1.0 pour une raison inconnue
                        angle = 1.57079633
                    else :
                        angle = asin(sin)

        ##            print("Angle : " + str(angle*180/3.14159))
                    list_angle.append(round(angle,8))

                    nb_virages +=1

        ##            layer_traj.changeAttributeValue(feat_traj.id(), idx_angle, angle)
        ##            layer_noeuds.changeAttributeValue(feat_traj.id(), idx_angle, angle)

        ##        elif (noeud_x == fin_traj_x and noeud_x == debut_traj_x):
        ##
        ##            angle = 0

                # elif (i == len(list_noeuds)):
                #     angle = 0
                # elif (i = len())
                else: #si on se situe pas a une extremite le cas est plus simple


                    noeud_avant_x = list_noeuds[i-1].geometry().asPoint().x()
                    noeud_avant_y = list_noeuds[i-1].geometry().asPoint().y()

        ##            print("noeud_avant_x : " + str(noeud_avant_x))
        ##            print("noeud_avant_y : " + str(noeud_avant_y))

                    noeud_apres_x = list_noeuds[i+1].geometry().asPoint().x()
                    noeud_apres_y = list_noeuds[i+1].geometry().asPoint().y()

        ##            print("noeud_apres_x : " + str(noeud_apres_x))
        ##            print("noeud_apres_y : " + str(noeud_apres_y))

                    sin = ((noeud_apres_x-noeud_x)*(noeud_y-noeud_avant_y)-(noeud_x-noeud_avant_x)*(noeud_apres_y-noeud_y))/(dist(noeud_x,noeud_y,noeud_avant_x,noeud_avant_y)*dist(noeud_apres_x,noeud_apres_y,noeud_x,noeud_y))
        ##            print sin
                    if (round(sin,1) == 1): #il y a une erreur lorsque le sinus vaut 1.0 pour une raison inconnue
        ##                print 'toto'
                        angle = 1.57079633 #angle de 90degres (extremite de la trajactoire)
                    else :
                        angle = asin(sin)

        ##            print("Angle : " + str(angle*180/3.14159))
                    list_angle.append(round(angle,8))

                    nb_virages +=1
                    # print nb_virages
                    # print angle*180/3.14159
        ##    print nb_virages

            #ajout d'un champ angle_rad a notre table de noeuds en entree
                percent = (i/float(count)) * 100
                progress.setValue(percent) #pour faire avancer la barre de progression
            layer_noeuds.startEditing()
            idx_angle_noeuds = layer_noeuds.fieldNameIndex("angle_rad")

            if (idx_angle_noeuds == -1):
                layer_noeuds.dataProvider().addAttributes( [QgsField("angle_rad", QVariant.Double ,'double', 20, 8)])
                layer_noeuds.updateFields()
                idx_angle_noeuds = layer_noeuds.fieldNameIndex("angle_rad")

            # on remplit les tables avec les angles calcules

            j = 0
            for feat_noeuds in layer_noeuds.getFeatures():
        ##        print list_angle[i]
        ##        print idx_angle_noeuds
                if list_angle[j] != 1.57079633: #on supprime les points extremes (ils ne font pas partis de l offset)
                    layer_noeuds.changeAttributeValue(feat_noeuds.id(), idx_angle_noeuds, list_angle[j])
                else:
                    layer_noeuds.deleteFeature(feat_noeuds.id())
                j+=1

            #application des modifications sur la couche
            layer_noeuds.updateExtents()
            layer_noeuds.commitChanges()

            layer_noeuds.removeSelection()
            iface.messageBar().clearWidgets()

        calcul_angle_consecutifs_offset(line_offset_noeuds, line_offset)

        print('Calcul de la longueur des lignes et suppression des lignes aux extremites (Offset)...')

        progressMessageBar = iface.messageBar().createMessage("Calcul de la longueur des lignes et suppression des lignes aux extremites (Offset)...")
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        iface.messageBar().pushWidget(progressMessageBar, iface.messageBar().INFO)

        line_offset.selectAll()

        #Count all selected feature
        count = line_offset.selectedFeatureCount()
        i=0

        line_offset.startEditing()
        line_offset_pr = line_offset.dataProvider()
        line_offset_pr.addAttributes( [QgsField("length", QVariant.Double, 'double', 20, 8)])
        line_offset.updateFields()

        idx = line_offset.fieldNameIndex('length')

        length_line_extremite = round(buffer_distance*sqrt(2),8) #pythagore

        for line in line_offset.getFeatures():
            length = line.geometry().length()

            length = round(length,8)
            line_offset.changeAttributeValue(line.id(), idx, length)

            if (length == length_line_extremite):
                line_offset.deleteFeature(line.id())

            percent = (i/float(count)) * 100
            progress.setValue(percent) #pour faire avancer la barre de progression
            i+=1

        #application des modifications sur la couche
        line_offset.updateExtents()
        line_offset.commitChanges()

        line_offset.removeSelection()
        iface.messageBar().clearWidgets()

        #ajout d'un champ empate a notre table de noeuds (0 ou 1 si empatement)
        traj_noeuds.startEditing()
        traj_noeuds_pr = traj_noeuds.dataProvider()
        traj_noeuds_pr.addAttributes( [QgsField("empate", QVariant.Int)])
        traj_noeuds.updateFields()
        idx_empate = traj_noeuds.fieldNameIndex("empate")


        print('Recherche des empatements...')
        progressMessageBar = iface.messageBar().createMessage("Recherche des empatements...")
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        iface.messageBar().pushWidget(progressMessageBar, iface.messageBar().INFO)

        traj_noeuds.selectAll()

        #Count all selected feature
        count = traj_noeuds.selectedFeatureCount()
        i = 0

        nb_empatement = 0
        for noeud_traj in traj_noeuds.getFeatures():

            percent = (i/float(count)) * 100
            progress.setValue(percent) #pour faire avancer la barre de progression

            request = QgsFeatureRequest().setFilterExpression( '"id" = \'%s\'' % noeud_traj["id"] )
        ##    if (nb_empatement != 0):
        ##        nb_empatement = 0
            list_empatement = list()
            empate = 0
            for noeud_offset in line_offset_noeuds.getFeatures(request):

        ##        print noeud['angle']
                angle_noeud_traj = noeud_traj['angle_rad']

        ##        print("angle_noeud_traj : " + str(angle_noeud_traj*180/3.14159))
                angle_noeud_offset = noeud_offset['angle_rad']
        ##        print("angle_noeud_offset : " + str(angle_noeud_offset*180/3.14159))

                if angle_noeud_traj == angle_noeud_offset or angle_noeud_traj == -angle_noeud_offset :
                    distance = QgsDistanceArea()
                    distance_noeud_traj_noeuds_offset = distance.measureLine(noeud_traj.geometry().asPoint(), noeud_offset.geometry().asPoint())

                    if (distance_noeud_traj_noeuds_offset >= coef_empatement*buffer_distance):
        ##                list_empatement.append(noeud_traj)
        ##                print distance_noeud_traj_noeuds_offset
                        empate = 1
                i+=1
            traj_noeuds.changeAttributeValue(noeud_traj.id(), idx_empate, empate)

        #application des modifications sur la couche
        traj_noeuds.updateExtents()
        traj_noeuds.commitChanges()

        traj_noeuds.removeSelection()
        iface.messageBar().clearWidgets()


        print('Comptage des empatements et ajout du resultat a la couche des trajectoires...')

        progressMessageBar = iface.messageBar().createMessage("Comptage des empatements et ajout du resultat a la couche des trajectoires...")
        progress = QProgressBar()
        progress.setMaximum(100)
        progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
        progressMessageBar.layout().addWidget(progress)
        iface.messageBar().pushWidget(progressMessageBar, iface.messageBar().INFO)

        layer_traj.selectAll()

        #Count all selected feature
        count = layer_traj.selectedFeatureCount()
        i = 0

        #ajout d'un champ nb_empat a notre table des trajectoires
        layer_traj.startEditing()

        idx_nb_empat = layer_traj.fieldNameIndex('nb_empat')

        if (idx_nb_empat == -1): #si le champs n'existe pas
            layer_traj_pr = layer_traj.dataProvider()
            layer_traj_pr.addAttributes( [QgsField("nb_empat", QVariant.Int)])
            layer_traj.updateFields()

        idx_nb_empat = layer_traj.fieldNameIndex('nb_empat')

        for traj in layer_traj.getFeatures():

            nb_empatement = 0
            request = QgsFeatureRequest().setFilterExpression( '"id" = \'%s\'' % traj["id"] )

            for noeud_traj in traj_noeuds.getFeatures(request):
                empate = noeud_traj['empate']
                if (empate==1):
                    nb_empatement += 1

            percent = (i/float(count)) * 100
            progress.setValue(percent) #pour faire avancer la barre de progression+

            layer_traj.changeAttributeValue(traj.id(), idx_nb_empat, nb_empatement)

        #application des modifications sur la couche
        layer_traj.updateExtents()
        layer_traj.commitChanges()

        layer_traj.removeSelection()
        iface.messageBar().clearWidgets()


        print('Export des trajectoires empatees...')
        iface.messageBar().createMessage("Export des trajectoires empatees...")
        request = QgsFeatureRequest().setFilterExpression( '"nb_empat" >= \'%d\'' % nb_min_empatement )

        it = layer_traj.getFeatures(request)
        ids = [i.id() for i in it] #select only the features for which the expression is true
        layer_traj.setSelectedFeatures(ids)

        processing.runalg('qgis:saveselectedfeatures', layer_traj, cheminEnregistrement +"/" + layer_traj.name() + "_empate.shp")
        iface.addVectorLayer(cheminEnregistrement + "/" + layer_traj.name() + "_empate.shp", layer_traj.name() + "_empate", "ogr")
        layer_traj.removeSelection()
