# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ScriptPreparer
                                 A QGIS plugin
 This plugin prepares ogr2ogr script from selected wfs and layers
                              -------------------
        begin                : 2017-09-23
        git sha              : https://github.com/giskonsulenten
        copyright            : (C) 2017 by Jesper Jøker Eg - GISkonsulenten
        email                : jesper@giskonsulenten.dk
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
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QFileDialog

import qgis, platform
from qgis.core import *

import owslib
from owslib.wfs import WebFeatureService

# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from script_preparer_dialog import ScriptPreparerDialog
import os.path

class ScriptPreparer:
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
            'ScriptPreparer_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = ScriptPreparerDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Script Preparer')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'ScriptPreparer')
        self.toolbar.setObjectName(u'ScriptPreparer')

        self.dlg.pushbuttonSetEnvelope.clicked.connect(self.get_area_of_interest)
        self.dlg.pushbuttonGetLayers.clicked.connect(self.getLayers)
        self.dlg.pushbuttonMakeScript.clicked.connect(self.makeScript)
        self.dlg.pushButtonDataStore.clicked.connect(self.DataStore)
        self.dlg.comboBox.currentIndexChanged.connect(self.dataFormat)
        self.dlg.outputFile.clicked.connect(self.outputFile)
        

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
        return QCoreApplication.translate('ScriptPreparer', message)


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

        icon_path = ':/plugins/ScriptPreparer/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Script Preparer'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Script Preparer'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def get_area_of_interest(self):
        ext = qgis.utils.iface.mapCanvas().extent()
        coord = str(int(ext.xMinimum())) + ' ' + str(int(ext.yMinimum()))  + ' ' + str(int(ext.xMaximum())) + ' ' + str(int(ext.yMaximum()))
        self.dlg.envelopeCoords.setText(coord)

    def getLayers(self):
        import urllib2, re
        url = self.dlg.wfsURL.text()
        if url.lower().find("?request=getcapabilities") == -1:
            url = url + "?request=GetCapabilities"
        if url.lower().find("&service=wfs") == -1:
            url = url + "&service=WFS"

        wfs = WebFeatureService(url=url)
        self.dlg.listWidget.clear()
        self.dlg.listWidget_2.clear()
        for l in list(wfs.contents):
            self.dlg.listWidget.addItem(l)

    def DataStore(self):
        self.dlg.connectionString.setText('')
        # Select existing folder for shape-files
        if self.dlg.comboBox.currentIndex()==0:
            self.dlg.filePathDataStore.setText('Pick a directory for shape files')
            filename = str(QFileDialog.getExistingDirectory(self.dlg, "Select existing directory for output"))
            self.dlg.filePathDataStore.setText(filename)
            outputPath, outputFilename = os.path.split(self.dlg.filePathDataStore.text())
            self.dlg.connectionString.setText('-f \"ESRI Shapefile\" ' + outputFilename)
            
        # Select existing db-files
        if self.dlg.comboBox.currentIndex()==1:
            Fdlg = QFileDialog()
            Fdlg.setFileMode(QFileDialog.ExistingFile)
            filename = str(Fdlg.getOpenFileName(self.dlg, "Select database file","", '*.sqlite'))
            self.dlg.filePathDataStore.setText(filename)
            outputPath, outputFilename = os.path.split(self.dlg.filePathDataStore.text())
            self.dlg.connectionString.setText('-f SQLite ' + outputFilename)
        if self.dlg.comboBox.currentIndex()==2:
            Fdlg = QFileDialog()
            Fdlg.setFileMode(QFileDialog.ExistingFile)
            filename = str(Fdlg.getOpenFileName(self.dlg, "Select database file","", '*.gpkg'))
            self.dlg.filePathDataStore.setText(filename)
            outputPath, outputFilename = os.path.split(self.dlg.filePathDataStore.text())
            self.dlg.connectionString.setText('-f GPKG ' + outputFilename)
            
        # Select existing fgdb files
        if self.dlg.comboBox.currentIndex()==3:
            Fdlg = QFileDialog()
            Fdlg.setFileMode(QFileDialog.ExistingFile)
            filename = str(Fdlg.getOpenFileName(self.dlg, "Select database file","", '*.gdb'))
            self.dlg.filePathDataStore.setText(filename)
            outputPath, outputFilename = os.path.split(self.dlg.filePathDataStore.text())
            self.dlg.connectionString.setText('-f \"FileGDB\" ' + outputFilename)
            

    def dataFormat(self):
        index = self.dlg.comboBox.currentIndex()		
        selection = self.dlg.comboBox.currentText()
        if index==0:
            self.dlg.filePathDataStore.setText('Pick a directory for shape files')
        if index==1:
            self.dlg.filePathDataStore.setText('Pick a SpatialLite database')
        if index==2:
            self.dlg.filePathDataStore.setText('Pick a GeoPackage database')
        if index==3:
            self.dlg.filePathDataStore.setText('Pick a esri File geodatabase')
        
        
    def outputFile(self):
        outFile = str(QFileDialog.getSaveFileName(self.dlg, "Select output script-file","", '*.*'))
        self.dlg.scriptFile.setText(outFile)

####################################################################################################################################
####################################################################################################################################
# makeScript
####################################################################################################################################
####################################################################################################################################
    
    def makeScript(self):
        self.dlg.listWidget_2.clear()
        selectedLayers=[]
        fileWritten=''
        inputComplete=''
        self.dlg.listWidget_2.addItem('Layers to process....')
        self.dlg.listWidget_2.addItem('')
        outputPath, outputFilename = os.path.split(self.dlg.filePathDataStore.text())
        osSystem =  platform.system()
        
        if self.dlg.envelopeCoords.text()=="Push 'Area Of Interest' to set area of interest from map window":
            self.dlg.envelopeCoords.setText('0 0 0 0')
        
        if len(self.dlg.connectionString.text())<=0:
            dialogText = "No connection string present"
            inputComplete='False'
            QMessageBox.critical(None,"Error", str(dialogText))
        
        if len(self.dlg.refSystem.text())<=0:
            dialogText = "No Ref-system string present"
            inputComplete='False'
            QMessageBox.critical(None,"Error", str(dialogText))
            
        if len(self.dlg.wfsURL.text())<=0:
            dialogText = "No URL string present"
            inputComplete='False'
            QMessageBox.critical(None,"Error", str(dialogText))
        
        if  inputComplete!='False' and len(self.dlg.listWidget.selectedItems())>0:        
            try:
                for item in self.dlg.listWidget.selectedItems():
                    self.dlg.listWidget_2.addItem(item.text())
                    selectedLayers.append('ogr2ogr -update -overwrite ' + self.dlg.connectionString.text() + ' -spat '
                     + self.dlg.envelopeCoords.text() + ' "' + 'WFS:' + self.dlg.wfsURL.text() + '" ' + item.text() + ' -nln ' + item.text().replace(":","_") + ' -t_srs "' + self.dlg.refSystem.text() + '"')
                 
                self.dlg.listWidget_2.addItem('')
                self.dlg.listWidget_2.addItem('Number of selected layers: ' + str(len(selectedLayers)))
            
            except:
                dialogText = "Error in input data - check your inputs"
                inputComplete='False'
                QMessageBox.critical(None,"Error", str(dialogText))

        elif len(self.dlg.listWidget.selectedItems())==0:
            dialogText = "No layers selected in Layers"
            QMessageBox.critical(None,"Error", str(dialogText))

        if self.dlg.scriptFile.text()!= 'Path to script file' and len(self.dlg.scriptFile.text()) > 0:
            f = open(self.dlg.scriptFile.text(),'w')
        
            if osSystem == 'Windows':
                if platform.architecture()[0] == '64bit':
                    f.write('c:\OSGeo4W64\OSGeo4W.bat' + '\n')
                    f.write(outputPath[:2] + '\n')
                    f.write('cd ' + outputPath[2:] + '\n')
                if platform.architecture()[0] == '32bit':
                    f.write('c:\OSGeo4W\OSGeo4W.bat' + '\n')
                    f.write(outputPath[:2] + '\n')
                    f.write('cd ' + outputPath[2:] + '\n')
            else:
                f.write('#!/bin/bash' + '\n')
                f.write('cd ' + outputPath + '\n')
            
            for i in selectedLayers:
                f.write(i + '\n')
                
            fileWritten='True'
        
            f.close
        
        
        if self.dlg.scriptFile.text()=='Path to script file' or len(self.dlg.scriptFile.text())==0:
            dialogText = "Error in script file path"
            QMessageBox.critical(None,"Error", str(dialogText))
        
        if fileWritten=='True':
            dialogText = "Script is ready"
            QMessageBox.information(None, "Info", str(dialogText))

        
    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

            
