from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QVBoxLayout
from PyQt6.QtCore import QThread, Qt

from db.db_manager import DatabaseManager

from GUI.data_display import DataDisplay
from GUI.control_panel import ControlPanel
from GUI.irt_plot import IRTPlot
from GUI.adquirido_plot import AdquiridoPlot
from threads.modbus_client8N1 import ModbusClient8N1
from threads.janitza_client8N2 import JanitzaClient8N2
from threads.arduinoVariacClient import arduinoVariac
from threads.adruino_stepper_worker import ArduinoStepperWorker
from data_handler import DataHandler
from GUI.test_controller import testController

from GUI.menu_bar import MainMenuBar
from GUI.metadata_dialog import MetadataDialog
from GUI.comp_dialog import CompDialog
from GUI.del_comp_dialog import DelCompDialog

class MainWindow(QMainWindow):
    def __init__(self, variables):
        super().__init__()
        self.metadata = {}
        self.ensayosComp = {}

        self.setWindowTitle("Software Banco Control Automatico V 1.0")

        # Central Widget
        central = QWidget()
        layout = QGridLayout()
        central.setLayout(layout)
        self.setCentralWidget(central)

        # --------------------------------------------------------------------------- #
        #  Widgets:
        self.data_display = DataDisplay(variables)
        self.control_panel = ControlPanel()
        self.pressure_irt = IRTPlot(title="Presion IRT", chosen_vars=["Pe", "Ps", "Ps-Pe"])

        self.pressure_acq = AdquiridoPlot(title="Presión Adquirida", y_label="Presión [mca]")
        self.potAcq = AdquiridoPlot(title="Potencia Adquirida",chosen_vars=["Pot1","Pot2","Pot3"], y_label="Pot [W]")
        self.corrienteAcq = AdquiridoPlot(title="Corriente Adquirida",chosen_vars=["I1","I2","I3"],y_label="I [A]")

        self.MenuBar = MainMenuBar(self)
        self.setMenuBar(self.MenuBar)
        self.MenuBar.open_metadata_requested.connect(self.show_metadata_window)
        self.MenuBar.agregarEnsayoRequested.connect(self.show_comp_window)
        self.MenuBar.quitarEnsayoRequested.connect(self.show_del_comp_window)
        # --------------------------------------------------------------------------- #
        
        self.rightWidget = QWidget()
        self.rightLayout = QGridLayout(self.rightWidget)
        self.rightLayout.addWidget(self.pressure_irt,0,0)
        self.rightLayout.addWidget(self.data_display,1,0)
        self.rightLayout.addWidget(self.control_panel,2,0)
        self.rightLayout.setRowStretch(0,2)
        self.rightLayout.setRowStretch(1,1)
        self.rightLayout.setRowStretch(2,1)

        self.acqGraphContainer = QWidget()
        self.acqGraphLayout = QGridLayout(self.acqGraphContainer)
        self.acqGraphLayout.addWidget(self.pressure_acq,0,0)
        self.acqGraphLayout.addWidget(self.potAcq,1,0)
        self.acqGraphLayout.addWidget(self.corrienteAcq,2,0)

        layout.addWidget(self.acqGraphContainer,0,0)
        layout.addWidget(self.rightWidget,0,1)
        layout.setColumnStretch(0,2)
        layout.setColumnStretch(1,3)

        # Data handler:
        db = DatabaseManager()
        self.data_handler = DataHandler(variables, db=db)
        self.data_handler.bombasList.connect(self.control_panel.populate_dropdown)
        
        self.control_panel.selectedBomba.connect(self.data_handler.change_bomba)
        self.control_panel.selectedEnsayo.connect(self.data_handler.chage_tipo_ensayo)
        self.control_panel.isMonofasico.connect(self.data_handler.changeMonofasico)
        self.data_handler.logMsg.connect(self.control_panel.logBox.appendPlainText)
        
        self.data_handler.load_bombas()

        # --------------------------------------------------------------------------- #
        # Thread 8N1:
        self.thread8N1 = QThread()
        self.client8N1 = ModbusClient8N1(variables)
        self.client8N1.moveToThread(self.thread8N1)

        self.thread8N1.started.connect(self.client8N1.start) # Arranca el timer del client
        self.client8N1.new_data.connect(self.data_handler.update_irt) # Datos nuevos desde 8N1 -> Data Handler

        self.control_panel.commandRequested.connect(self.client8N1.handleCommand) # Conecta el client con los comandos del PLC
        self.control_panel.changeFrecuency.connect(self.client8N1.change_frec) # Conecta el cambio de frecuencia
        self.control_panel.changeCaudalimetro.connect(self.client8N1.change_caudalimetro) # Conecta el cambio de caudalimetro

        # --------------------------------------------------------------------------- #
        # Thread 8N2:
        self.thread8N2 = QThread()
        self.client8N2 = JanitzaClient8N2(variables)
        self.client8N2.moveToThread(self.thread8N2)

        self.thread8N2.started.connect(self.client8N2.start)
        self.client8N2.janitzaDataReady.connect(self.data_handler.update_irt)
        
        # --------------------------------------------------------------------------- #
        #Thread Arduino Variac:
        self.variacThread = QThread()
        self.variacClient = arduinoVariac()
        self.variacClient.moveToThread(self.variacThread)

        self.variacThread.started.connect(self.variacClient.start)
        self.control_panel.setVoltageRequested.connect(self.variacClient.set_target_voltage,Qt.ConnectionType.QueuedConnection)
        self.variacClient.logMessage.connect(self.control_panel.logBox.appendPlainText)
        
        # --------------------------------------------------------------------------- #
        # Adquisiocion Auto/Semi-Auto:
        # --------------------------------------------------------------------------- #
        self.testController = testController()
        self.stepperThread = QThread()
        self.stepperClient = ArduinoStepperWorker()
        self.stepperClient.moveToThread(self.stepperThread)

        self.stepperThread.started.connect(self.stepperClient.start)
        self.stepperClient.log.connect(self.control_panel.logBox.appendPlainText)
        self.testController.logMsg.connect(self.control_panel.logBox.appendPlainText)
        self.control_panel.enableStepper.connect(self.stepperClient.set_stepper_enable)
        self.control_panel.enableStepper.connect(self.client8N1.auto_toggle)
        self.control_panel.requestHoming.connect(self.stepperClient.request_homing)
        self.stepperClient.homingLimitsReceived.connect(self.testController.automatic_parameters)
        self.testController.homingFinished.connect(self.control_panel.home_valve)
        self.stepperClient.Qack.connect(self.data_handler.update_irt)

        self.data_handler.stepAcq.connect(self.testController.next_step)
        self.testController.nextStep.connect(self.stepperClient.set_target_flow)
        self.testController.nextStep.connect(self.data_handler.update_target)
        self.control_panel.autoStart.connect(self.testController.next_step)
        self.testController.autoStepFinished.connect(self.data_handler.guardar_datos_auto)
        # --------------------------------------------------------------------------- #

        # Adquirir punto:
        #self.control_panel.savePointRequested.connect(self.data_handler.adquirir_datos) # boton a data_handler
        self.control_panel.savePointRequested.connect(lambda: self.data_handler.adquirir_datos(self.data_display.get_manual_data()))
        self.control_panel.guardarDatosRequested.connect(self.data_handler.guardar_datos) # Guardar Datos: control_panel -> data handler
        self.control_panel.borrarUltimo.connect(self.data_handler.borrar_ultimo) # Borrar Ultimo: Control Panel a Data Handler
        self.control_panel.borrarTodo.connect(self.data_handler.borrar_todo) # Borrar Todo: Control Panel a Data Handler

        # Borrar todo:
        self.control_panel.borrarTodo.connect(self.pressure_acq.borrar_todo)
        self.control_panel.borrarTodo.connect(self.potAcq.borrar_todo)
        self.control_panel.borrarTodo.connect(self.corrienteAcq.borrar_todo)

        self.MenuBar.borrarTodosRequested.connect(self.pressure_acq.borrar_todos_comp)
        self.MenuBar.borrarTodosRequested.connect(self.potAcq.borrar_todos_comp)
        self.MenuBar.borrarTodosRequested.connect(self.corrienteAcq.borrar_todos_comp)

        # Actualiza los plots acq
        self.data_handler.pointAcquired.connect(self.pressure_acq.update_adquirido) # Data Handler -> Plot
        self.data_handler.pointAcquired.connect(self.potAcq.update_adquirido) # Data Handler -> Plot
        self.data_handler.pointAcquired.connect(self.corrienteAcq.update_adquirido) # Data Handler -> Plot

        self.data_handler.stdAcquired.connect(self.pressure_acq.update_error_bars)
        self.data_handler.stdAcquired.connect(self.potAcq.update_error_bars)
        self.data_handler.stdAcquired.connect(self.corrienteAcq.update_error_bars)

        # Data Handler -> Display IRT
        self.data_handler.dataUpdated.connect(self.data_display.update_data)
        self.data_handler.bufferUpdated.connect(self.pressure_irt.update_buffer)

        self.thread8N1.start()
        self.thread8N2.start()
        self.variacThread.start()
        self.stepperThread.start()

        self.showMaximized()

    def show_metadata_window(self):
        bomba = self.control_panel.dropdownBombas.currentText()
        dialog = MetadataDialog(self,bomba)
        dialog.show()
        if dialog.exec():
            self.metadata = dialog.get_metadata()
            self.data_handler.update_metadata(self.metadata)

    def show_comp_window(self):
        dialog = CompDialog(self)
        dialog.show()
        if dialog.exec():
            ensayosComp = dialog.get_data_comp()
            self.ensayosComp = ensayosComp
            dataDict = {}
            for ensayo in list(ensayosComp.keys()):
                dataDict[ensayo] = ensayosComp[ensayo]["datos"]
            
            # Manda los datos a los objetos de graficos adquiridos:
            self.pressure_acq.agregar_comp(dataDict,"Ps-Pe")
            self.potAcq.agregar_comp(dataDict,"Pot. Total")
            self.corrienteAcq.agregar_comp(dataDict,"It")

    def show_del_comp_window(self):
        dialog = DelCompDialog(self,list(self.ensayosComp.keys()))
        dialog.show()
        if dialog.exec():
            delEnsayos = dialog.get_ensayos_del()
            
            self.pressure_acq.borrar_n_comp(delEnsayos)
            self.potAcq.borrar_n_comp(delEnsayos)
            self.corrienteAcq.borrar_n_comp(delEnsayos)
            for ensayo in delEnsayos:
                del self.ensayosComp[ensayo]
