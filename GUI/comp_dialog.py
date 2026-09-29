from PyQt6.QtWidgets import (
    QDialog, QGridLayout, QComboBox, QLabel,
    QPushButton, QPlainTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt
import json
import os

class CompDialog(QDialog):
    def __init__(self, parent=None, bomba=None):
        super().__init__(parent)
        filePath = os.path.join("ArchivosAuxiliares","datos_ensayos.json")
        # with open("Archivos Auxiliares/bombas.json","r") as f:
        with open(filePath,"r") as f:
            self.ensayosData = json.load(f)
        self.bombaSelected = None
        self.ensayoSelected = None
        self.dictEnsayosSelected = {}

        self.setWindowTitle("Comparación de Ensayos IRT")
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
    # Seleccion de bomba
    # ======================================== #
        label = QLabel(self,text="Bomba: ")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,0 ,0)
        self.bombaSelect = QComboBox()
        self.bombaSelect.addItems(["Seleccione una Bomba"])
        self.bombaSelect.addItems(list(self.ensayosData.keys()))
        self.bombaSelect.currentIndexChanged.connect(self.select_bomba)
        layout.addWidget(self.bombaSelect,0,1)

    # ======================================== #
    # Seleccion de Ensayo
    # ======================================== #
        label = QLabel(self,text="Ensayo: ")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,1 ,0)
        self.ensayoSelect = QComboBox()
        self.ensayoSelect.currentTextChanged.connect(self.select_ensayo)
        layout.addWidget(self.ensayoSelect,1,1)

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
        
    def select_bomba(self):
        self.ensayoSelect.clear()
        bomba = self.bombaSelect.currentText()
        if bomba == "Seleccione una Bomba":
            return
        self.bombaSelected = bomba
        self.ensayoSelect.addItems(list(self.ensayosData[bomba].keys()))

    def select_ensayo(self):
        self.ensayoSelected = self.ensayoSelect.currentText()

    def agregar_ensayo(self):
        ensayo = self.ensayoSelected
        if ensayo in self.dictEnsayosSelected.keys():
            self.logBox.appendPlainText(f"Ya se agrego el ensayo {ensayo}")
            return
        self.logBox.appendPlainText(f"Se agrega el ensayo {ensayo}")
        bomba = self.bombaSelected
        selectedEnsayo = self.ensayosData[bomba][ensayo]
        self.dictEnsayosSelected[ensayo] = selectedEnsayo
        self.logBox.appendPlainText(f"Ensayos seleccionados: {', '.join(list(self.dictEnsayosSelected.keys()))}")
    
    def get_data_comp(self):
        return self.dictEnsayosSelected