from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QComboBox, QLabel,
    QPushButton, QFormLayout, QLineEdit
)
from PyQt6.QtCore import Qt
import json
import os

class MetadataDialog(QDialog):
    def __init__(self, parent=None, bomba=None):
        super().__init__(parent)
        filePath = os.path.join("ArchivosAuxiliares","bombas.json")
        # with open("Archivos Auxiliares/bombas.json","r") as f:
        with open(filePath,"r") as f:
            self.bombasData = json.load(f)
        self.metadata = {}
        self.bomba = bomba

        self.setWindowTitle("Características del Ensayo")
        self.setMinimumWidth(350)
        layout = QGridLayout()
        self.setLayout(layout)

        label = QLabel(self,text="Bomba: "+bomba)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,0 ,0)
    # ======================================== #
    # Turbina
    # ======================================== #
        label = QLabel(parent=self,text="Turbina:")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,1 ,0)
        self.turbinaModelo = QComboBox()
        self.turbinaModelo.addItems(["","TMA","Tango","30 Alabes","Bronce"])
        layout.addWidget(self.turbinaModelo,1,1)
        label = QLabel(parent=self,text=" Ø:")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,1 ,2)
        self.turbinaDiam = QLineEdit()
        layout.addWidget(self.turbinaDiam,1,3)

    # ======================================== #
    # Bobinado
    # ======================================== #
        label = QLabel(parent=self,text="Bobinado:")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,2 ,0)
        self.bobinado = QLineEdit()
        self.bobinado.setText("STD")
        layout.addWidget(self.bobinado,2,1)

    # ======================================== #
    # Control
    # ======================================== #
        label = QLabel(parent=self,text="Control:")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label, 3, 0)
        self.control = QComboBox()
        self.control.addItems(["NO","ECO Tango","ECO Max","RPX","FLP","FL","Press E"])
        layout.addWidget(self.control,3,1)

    # ======================================== #
    # Caracol
    # ======================================== #
        label = QLabel(parent=self,text="Caracol:")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,4,0)
        self.caracol = QComboBox()
        self.caracol.addItems(["","Tango","Max VSTD","Max VSTD 1.5\"","Max VAC 1\"","Max VAC 1.5\"",
                                "4-1","7-1","15-1","15-1 Con Adaptador","Intelig"])
        layout.addWidget(self.caracol,4,1)
    
    # ======================================== #
    # Capacitor
    # ======================================== #
        label = QLabel(parent=self,text="Capacitor:")
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,5,0)
        self.capacitor = QLineEdit()
        layout.addWidget(self.capacitor,5,1)
    
    # ======================================== #
    # Botones
    # ======================================== #
        self.saveBtn = QPushButton("Guardar")
        self.closeBtn = QPushButton("Cerrar")
        self.saveBtn.clicked.connect(self.accept)
        self.closeBtn.clicked.connect(self.close)
        layout.addWidget(self.saveBtn,6,0)
        layout.addWidget(self.closeBtn,6,1)
    
    # ======================================== #
    # Texto y opciones dafault
    # ======================================== #
        multietapa_lista = ["Multietapa P60 - TANGO", "Multietapa P60 - INTELIG", "Multietapa P90 - TANGO","Multietapa P90 - INTELIG"]
        if bomba!= "Ninguna - Generica" and bomba not in multietapa_lista:
            dataBomba = self.bombasData[bomba]
            if "Capa Nominal" in dataBomba:
                self.capacitor.setText(dataBomba["Capa Nominal"])
            else:
                self.capacitor.setEnabled(False)
            self.caracol.setCurrentText(dataBomba["Caracol"])
            self.turbinaModelo.setCurrentText(dataBomba["Turbina"])
            self.turbinaDiam.setText(str(dataBomba["Diametro Turbina"]))
    
    def get_metadata(self):
        bomba = self.bomba
        if bomba == "Ninguna - Generica":
            return None
        metadata = self.bombasData[bomba]
        metadata["Turbina"] = self.turbinaModelo.currentText()
        metadata["Diametro Turbina"] = self.turbinaDiam.text()
        metadata["Bobinado"] = self.bobinado.text()
        metadata["Control"] = self.control.currentText()
        metadata["Caracol"] = self.caracol.currentText()
        if "uF" in self.capacitor.text():
            metadata["Capa Nominal"] = self.capacitor.text()[:-2]
        else:
            metadata["Capa Nominal"] = self.capacitor.text()
        return metadata