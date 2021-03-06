# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PluginEmpatement
                                 A QGIS plugin
 Ce plugin cherche les empâtements sur des polylignes
                             -------------------
        begin                : 2017-03-14
        copyright            : (C) 2017 by Léo Darengosse
        email                : leo.darengosse@gmail.com
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
    """Load PluginEmpatement class from file PluginEmpatement.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .plugin_empatement import PluginEmpatement
    return PluginEmpatement(iface)
