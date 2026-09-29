from PyQt6.QtWidgets import QMenuBar
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import pyqtSignal


class MainMenuBar(QMenuBar):
    open_metadata_requested = pyqtSignal()
    agregarEnsayoRequested = pyqtSignal()
    quitarEnsayoRequested = pyqtSignal()
    borrarTodosRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # ===== Caracteristicas ===== #
        caracteristicasMenu = self.addMenu("Características")
        cargarAction = QAction("Cargar Características",self)
        cargarAction.triggered.connect(self.open_metadata_requested)
        caracteristicasMenu.addAction(cargarAction)

        # ===== Comparaciones ===== #
        compMenu = self.addMenu("Comparar")
        agregarEnsayoAction = QAction("Agregar Ensayo",self)
        agregarEnsayoAction.triggered.connect(self.agregarEnsayoRequested)
        compMenu.addAction(agregarEnsayoAction)
        quitarEnsayoAction = QAction("Quitar Ensayo", self)
        quitarEnsayoAction.triggered.connect(self.quitarEnsayoRequested)
        compMenu.addAction(quitarEnsayoAction)
        borrarTodosAction = QAction("Borrar Todos",self)
        borrarTodosAction.triggered.connect(self.borrarTodosRequested)
        compMenu.addAction(borrarTodosAction)
