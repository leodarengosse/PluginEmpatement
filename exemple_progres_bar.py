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