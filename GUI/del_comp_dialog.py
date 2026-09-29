from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QComboBox, QLabel,
    QPushButton, QPlainTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt
import json
import os

class DelCompDialog(QDialog):
    def __init__(self, parent=None, ensayos:list = None):
        super().__init__(parent)
        self.ensayoSelected = None
        self.listEnsayosSelected = []

        self.setWindowTitle("Borrar Ensayos de Comparación")
        self.setMinimumWidth(400)
        layout = QGridLayout()
        self.setLayout(layout)

    # ======================================== #
    # Textbox
    # ======================================== #
        self.logBox = QPlainTextEdit(self)
        self.logBox.setReadOnly(True)
        layout.addWidget(self.logBox,0,2,3,1)

    # ======================================== #
    # Seleccion de Ensayos
    # ======================================== #
        label = QLabel(self,text="Ensayo: ")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,0 ,0)
        self.ensayoSelect = QComboBox()
        self.ensayoSelect.addItems(ensayos)
        layout.addWidget(self.ensayoSelect,0,1)

    # ======================================== #
    # Botones
    # ======================================== #
        self.saveBtn = QPushButton("Guardar")
        self.closeBtn = QPushButton("Cerrar")
        self.addBtn = QPushButton("Agregar")
        self.saveBtn.clicked.connect(self.accept)
        self.closeBtn.clicked.connect(self.close)
        self.addBtn.clicked.connect(self.agregar_ensayo)
        layout.addWidget(self.addBtn,3,0)
        layout.addWidget(self.saveBtn,3,1)
        layout.addWidget(self.closeBtn,3,2)

    def agregar_ensayo(self):
        self.ensayoSelected = self.ensayoSelect.currentText()
        ensayo = self.ensayoSelected
        if ensayo in self.listEnsayosSelected:
            self.logBox.appendPlainText(f"Ya se agrego el ensayo {ensayo}")
            return
        self.logBox.appendPlainText(f"Se agrega el ensayo {ensayo}")
        self.listEnsayosSelected.append(ensayo)
        self.logBox.appendPlainText(f"Ensayos seleccionados: {', '.join(self.listEnsayosSelected)}")
    
    def get_ensayos_del(self):
        return self.listEnsayosSelected
