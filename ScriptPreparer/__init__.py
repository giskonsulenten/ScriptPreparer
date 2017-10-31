# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ScriptPreparer
                                 A QGIS plugin
 This plugin prepares ogr2ogr script from selected wfs and layers
                             -------------------
        begin                : 2017-09-23
        copyright            : (C) 2017 by Jesper Jøker Eg - GISkonsulenten
        email                : jesper@giskonsulenten.dk
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ScriptPreparer class from file ScriptPreparer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .script_preparer import ScriptPreparer
    return ScriptPreparer(iface)
