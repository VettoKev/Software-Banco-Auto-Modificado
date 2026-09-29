from PyQt6.QtWidgets import QWidget, QPushButton, QSlider, QLabel, QGridLayout, QComboBox, QLineEdit, QPlainTextEdit, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6_SwitchControl import SwitchControl
from plc_commands import PLC_COMMANDS
import json
import os

class ControlPanel(QWidget):
    commandRequested = pyqtSignal(dict)
    savePointRequested = pyqtSignal()
    guardarDatosRequested = pyqtSignal()
    changeFrecuency = pyqtSignal()
    changeCaudalimetro = pyqtSignal(int)
    borrarUltimo = pyqtSignal()
    borrarTodo = pyqtSignal()
    selectedBomba = pyqtSignal(str)
    selectedEnsayo = pyqtSignal(str)
    isMonofasico = pyqtSignal(bool)
    setVoltageRequested = pyqtSignal(float)
    enableStepper = pyqtSignal(int)
    requestHoming = pyqtSignal()
    autoStart = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.ensayoAuto = False
        self.valveHoming = False
        self.autoInProgress = False

        layout = QGridLayout()
        self.setLayout(layout)
        total_cols = 7

        self.logBox = QPlainTextEdit(self)
        self.logBox.setReadOnly(True)
        layout.addWidget(self.logBox,0,total_cols-1,4,1)
        
        self.habilitarEnergiaBtn = QPushButton("Habilitar Energia")
        layout.addWidget(self.habilitarEnergiaBtn,0,0)
        self.set_button_style(self.habilitarEnergiaBtn,"primary")
        self.habilitarEnergiaBtn.clicked.connect(lambda _, k="Habilitar Energia": self.commandRequested.emit(PLC_COMMANDS[k]))
        self.habilitarEnergiaBtn.clicked.connect(lambda: self.logBox.appendPlainText("Habilitar Energia")) 

        self.cortarEnergiaBtn = QPushButton("Cortar Energia")
        layout.addWidget(self.cortarEnergiaBtn,0,1)
        self.set_button_style(self.cortarEnergiaBtn,"primary")
        self.cortarEnergiaBtn.clicked.connect(lambda _, k="Cortar Energia": self.commandRequested.emit(PLC_COMMANDS[k]))
        self.cortarEnergiaBtn.clicked.connect(lambda: self.logBox.appendPlainText("Cortar Energia"))  
    
    # --------------------------
    #   Btn de Cambio de Frec
    # --------------------------
        self.frec_50Hz = True
        self.frecBtn = QPushButton("50 Hz")
        layout.addWidget(self.frecBtn,0,2)
        self.set_button_style(self.frecBtn,"idle")
        self.frecBtn.clicked.connect(self.changeFrec)

    # --------------------------
    #   Btn de Cambio de Caudalimetro
    # --------------------------
        self.cambioCaudalimetroBtn = QPushButton("Caudalimetro 2")
        self.Caudalimetro = 2
        layout.addWidget(self.cambioCaudalimetroBtn,1,2)
        self.set_button_style(self.cambioCaudalimetroBtn, "secondary")
        self.cambioCaudalimetroBtn.clicked.connect(self.changeCaudalimetroFunc)

    # --------------------------
    #   Btn de Tomar Datos
    # --------------------------
        self.tomarDatosBtn = QPushButton("Tomar datos")
        self.tomarDatosBtn.clicked.connect(self.savePointRequested.emit)
        layout.addWidget(self.tomarDatosBtn, 0, 3)
        self.set_button_style(self.tomarDatosBtn,"success")

    # --------------------------
    #   Btn de Guardar Datos
    # --------------------------
        self.guardarDatosBtn = QPushButton("Guardar Datos")
        self.guardarDatosBtn.clicked.connect(self.guardarDatosRequested.emit)
        layout.addWidget(self.guardarDatosBtn, 1, 3)
        self.set_button_style(self.guardarDatosBtn,"warning")

    # --------------------------
    #   Btn de Borrar Utlimos Datos
    # --------------------------
        borrarUltimoBtn = QPushButton("Borrar Ultimo")
        borrarUltimoBtn.clicked.connect(self.borrarUltimo.emit)
        layout.addWidget(borrarUltimoBtn, 0, 5)
        self.set_button_style(borrarUltimoBtn,"warning")

    # --------------------------
    #   Btn de Borrar Todos los Datos
    # --------------------------
        borrarTodoBtn = QPushButton("Borrar Todo")
        borrarTodoBtn.clicked.connect(self.borrarTodo.emit)
        layout.addWidget(borrarTodoBtn, 1, 5)
        self.set_button_style(borrarTodoBtn,"danger")

    # --------------------------
    #   Dropdown Bomba
    # --------------------------
        # filePath = os.path.join("ArchivosAuxiliares","bombas.json")
        # # with open("Archivos Auxiliares/bombas.json","r") as f:
        # with open(filePath,"r") as f:
        #     self.bombasData = json.load(f)
        self.dropdownBombas = QComboBox()
        self.dropdownBombas.addItems(["Ninguna - Generica"])
        # self.dropdownBombas.addItems(list(self.bombasData.keys()))
        layout.addWidget(self.dropdownBombas,0, 4)
        self.dropdownBombas.currentTextChanged.connect(self.select_bomba)

    # --------------------------
    #   Dropdown Tipo Ensayo
    # --------------------------
        self.tipoEnsayoDropdown = QComboBox()
        self.tipoEnsayoDropdown.addItems(["Curva Caracteristica", "Perdida de Carga", "Regimen Termico", "Vacio", "NPSH"])
        layout.addWidget(self.tipoEnsayoDropdown, 1, 4)
        self.tipoEnsayoDropdown.currentTextChanged.connect(self.select_ensayo)

    # ---------------------------------------------------------------------------#
    # Botones de arranque y parada:
        # track internal state
        self.active_mode = None  # "1ph", "3ph", or None
        self.btn_1ph = QPushButton("Arranque Monofasico")
        self.btn_3ph = QPushButton("Arranque Trifasico")

        self.set_button_style(self.btn_1ph,"primary")
        self.set_button_style(self.btn_3ph,"primary")

        layout.addWidget(self.btn_1ph, 1, 0)
        layout.addWidget(self.btn_3ph, 1, 1)

        self.btn_1ph.clicked.connect(self.handle_1ph)
        self.btn_3ph.clicked.connect(self.handle_3ph)

    # --------------------------
    #   Slider Tension
    # --------------------------
        label = QLabel(parent=self,text="Tensión:")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,3 ,0)
        self.TensionSlider = QSlider(Qt.Orientation.Horizontal)
        self.TensionSlider.setRange(0,250)
        self.TensionSlider.setValue(220)
        self.TensionSlider.valueChanged.connect(self.on_slider_change)
        self.TensionEntry = QLineEdit()
        self.TensionEntry.setText("220")
        self.TensionEntry.returnPressed.connect(self.on_entry_change)

        layout.addWidget(self.TensionSlider, 3, 1)
        layout.addWidget(self.TensionEntry, 3, 2)

        for i in range(0,total_cols-1):
            layout.setColumnStretch(i, 1)
        layout.setColumnMinimumWidth(total_cols-1,250)
    # --------------------------
    #   Switches Auto
    # --------------------------
        self.autoToggle = SwitchControl()
        self.autoToggle.setChecked(False)
        self.autoToggle.toggled.connect(self.on_toggle_auto)
        layout.addWidget(self.autoToggle,2,5)
        label = QLabel(parent=self,text="Ensayo Automatico")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,2 ,4)

        self.semiautoToggle = SwitchControl()
        self.semiautoToggle.setChecked(False)
        self.semiautoToggle.setEnabled(False)
        layout.addWidget(self.semiautoToggle,3,5)
        label = QLabel(parent=self,text="Ensayo Semi-Automatico")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(label,3 ,4)
    
    # --------------------------
    #   Controles Automatico
    # --------------------------
        # Origen Valvula
        self.homeValveBtn = QPushButton("Origen Valvula")
        self.set_button_style(self.homeValveBtn,"disabled")
        self.homeValveBtn.clicked.connect(self.home_valve)
        layout.addWidget(self.homeValveBtn,2,0)

        # Comenzar Ensayo Automatico
        self.startAutoBtn = QPushButton("Start Ensayo Auto")
        self.set_button_style(self.startAutoBtn,"disabled")
        self.startAutoBtn.clicked.connect(self.auto_start_func)
        layout.addWidget(self.startAutoBtn,2,1)

        # Next Step Semiauto
        self.nextStepBtn = QPushButton("Próximo Punto")
        self.set_button_style(self.nextStepBtn,"disabled")
        layout.addWidget(self.nextStepBtn,2,2)

        # --------------------------
        #   Campos Manuales: RPM e I_disp
        # --------------------------
        # Contenedor RPM (Fila 2, Columna 3 - abajo de Guardar Datos)
        layout_rpm = QHBoxLayout()
        label_rpm = QLabel(parent=self, text="RPM:")
        label_rpm.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.rpmEntry = QLineEdit(self)
        self.rpmEntry.setText("0.0")
        layout_rpm.addWidget(label_rpm)
        layout_rpm.addWidget(self.rpmEntry)
        layout.addLayout(layout_rpm, 2, 3)

        # Contenedor I Display (Fila 3, Columna 3 - abajo de RPM)
        layout_idisp = QHBoxLayout()
        label_idisp = QLabel(parent=self, text="I Display:")
        label_idisp.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.iDispEntry = QLineEdit(self)
        self.iDispEntry.setText("0.0")
        layout_idisp.addWidget(label_idisp)
        layout_idisp.addWidget(self.iDispEntry)
        layout.addLayout(layout_idisp, 3, 3)
# ============================================================================== #
#   Funciones
# ============================================================================== #
    def on_toggle_auto(self):
        if self.ensayoAuto:
            self.logBox.appendPlainText("Ensayo Manual")
            self.ensayoAuto = False
        # Deshabilitar Controles del Automatico
            self.set_button_style(self.homeValveBtn,"disabled")
            self.set_button_style(self.startAutoBtn,"disabled")
            self.set_button_style(self.nextStepBtn,"disabled")
            self.enableStepper.emit(0) # Deshabilitar Stepper cmd
            self.semiautoToggle.setEnabled(False)
        # Habilitar controles del manual
            self.set_button_style(self.tomarDatosBtn,"success")
            self.set_button_style(self.guardarDatosBtn,"warning")

        else:
            self.logBox.appendPlainText("Ensayo Automatico (solo testeo de origen y enable)")
            self.ensayoAuto = True
        # Habilitar Controles del Automatico
            self.set_button_style(self.homeValveBtn,"primary")
            self.set_button_style(self.startAutoBtn,"success")
            self.set_button_style(self.nextStepBtn,"success")
            self.enableStepper.emit(1) # Habilitar Stepper cmd
            self.semiautoToggle.setEnabled(True)
        # Deshabilitar controles del manual
            self.set_button_style(self.tomarDatosBtn,"disabled")
            self.set_button_style(self.guardarDatosBtn,"disabled")

    def auto_start_func(self):
        if self.autoInProgress:
            self.autoInProgress = False
            self.enableStepper.emit(0)
            self.set_button_style(self.homeValveBtn,"primary")
            self.set_button_style(self.startAutoBtn,"success")
            self.startAutoBtn.setText("Start Ensayo Auto")
            self.set_button_style(self.nextStepBtn,"success")
        else:
        # Arranca/Está en progreso el ensayo automatico
            self.autoInProgress = True
            self.enableStepper.emit(1)
            self.autoStart.emit()
            self.set_button_style(self.homeValveBtn,"disabled")
            self.set_button_style(self.nextStepBtn,"disabled")
            self.set_button_style(self.startAutoBtn,"danger")
            self.startAutoBtn.setText("Detener Ensayo")

    def on_slider_change(self,value):
        self.TensionEntry.setText(str(value))

    def on_entry_change(self):
        try:
            v = float(self.TensionEntry.text())
        except ValueError:
            return
        self.TensionSlider.setValue(int(v))
        self.setVoltageRequested.emit(float(v))
        self.logBox.appendPlainText("Tensión seteada a "+str(v)+" V")

    # =====================================
    #   Button logic handlers
    # =====================================
    def home_valve(self):
        if self.valveHoming is True:
            self.set_button_style(self.homeValveBtn,"primary")
            self.set_button_style(self.startAutoBtn,"success")
            self.set_button_style(self.nextStepBtn,"success")
            self.valveHoming = False
        else:
            self.valveHoming = True
            self.set_button_style(self.homeValveBtn,"disabled")
            self.set_button_style(self.startAutoBtn,"disabled")
            self.set_button_style(self.nextStepBtn,"disabled")
            self.logBox.appendPlainText("Origen del Stepper Solicitado")
            self.requestHoming.emit()

    def handle_1ph(self):
        if self.active_mode == "1ph":
            # Stop
            self.commandRequested.emit(PLC_COMMANDS["Parar Monofasico"])
            self.logBox.appendPlainText("Parar Monofasico")
            self.reset_buttons()
            return

        # Start
        self.commandRequested.emit(PLC_COMMANDS["Arranque Monofasico"])
        self.logBox.appendPlainText("Arranque Monofasico")
        self.isMonofasico.emit(True)
        self.active_mode = "1ph"

        self.btn_1ph.setText("Parar Monofasico")
        self.set_button_style(self.btn_1ph, "danger")

        # Disable 3ph y frecBtn
        self.set_button_style(self.btn_3ph, "disabled")
        self.set_button_style(self.frecBtn, "disabled")

    def handle_3ph(self):
        if self.active_mode == "3ph":
            # Stop
            self.commandRequested.emit(PLC_COMMANDS["Parar Trifasico"])
            self.logBox.appendPlainText("Parar Trifasico")
            self.reset_buttons()
            return

        # Start
        self.commandRequested.emit(PLC_COMMANDS["Arranque Trifasico"])
        self.logBox.appendPlainText("Arranque Trifasico")
        self.isMonofasico.emit(False)
        self.active_mode = "3ph"

        self.btn_3ph.setText("Parar Trifasico")
        self.set_button_style(self.btn_3ph, "danger")

        # Disable 1ph y frecBtn
        self.set_button_style(self.btn_1ph, "disabled")
        self.set_button_style(self.frecBtn, "disabled")

    # --------------------------
    #   Reset everything
    # --------------------------
    def reset_buttons(self):
        self.active_mode = None

        self.btn_1ph.setText("Arranque Monofasico")
        self.set_button_style(self.btn_1ph, "idle")

        self.btn_3ph.setText("Arranque Trifasico")
        self.set_button_style(self.btn_3ph, "idle")

        self.set_button_style(self.frecBtn, "idle")
    
    # --------------------------
    #   Change Frecuency
    # --------------------------
    def changeFrec(self):
        self.changeFrecuency.emit()
        if self.frec_50Hz:
            self.frecBtn.setText("60 Hz")
            self.set_button_style(self.frecBtn,"danger")
            self.logBox.appendPlainText("Cambio a 60 Hz")
            self.frec_50Hz = False
        else:
            self.frecBtn.setText("50 Hz")
            self.logBox.appendPlainText("Cambio a 50 Hz")
            self.set_button_style(self.frecBtn,"idle")
            self.frec_50Hz = True

    # --------------------------
    #   Change Caudalimetro
    # --------------------------
    def changeCaudalimetroFunc(self):
        if self.Caudalimetro == 2:
            self.cambioCaudalimetroBtn.setText("Caudalimetro 1")
            self.logBox.appendPlainText("Cambio a Caudalimetro 1")
            self.set_button_style(self.cambioCaudalimetroBtn,"light")
            self.Caudalimetro = 1
        elif self.Caudalimetro == 1:
            self.cambioCaudalimetroBtn.setText("Caudalimetro 2")
            self.logBox.appendPlainText("Cambio a Caudalimetro 2")
            self.set_button_style(self.cambioCaudalimetroBtn,"secondary")
            self.Caudalimetro = 2
        self.changeCaudalimetro.emit(self.Caudalimetro)

    # --------------------------
    #   Populate Dropdown
    # --------------------------
    def populate_dropdown(self,bombasList: list):
        print("entra en populate_dropdown")
        filePath = os.path.join("ArchivosAuxiliares","bombas.json")
        with open(filePath,"r") as f:
            bombasData = json.load(f)
        for item in bombasData:
            if item not in bombasList:
                print(f"Se agrega {item} a la lista")
                bombasList.append(item)
        bombasList.sort()
        self.dropdownBombas.addItems(bombasList)

    # --------------------------
    #   Select Bomba
    # --------------------------
    def select_bomba(self,bomba):
        if bomba == "Ninguna - Generica":
            self.selectedBomba.emit(None)
        else:
            self.selectedBomba.emit(bomba)

    # --------------------------
    #   Select Tipo Ensayo
    # --------------------------
    def select_ensayo(self,ensayo):
        self.selectedEnsayo.emit(ensayo)

    # --------------------------
    #   Utility: button style
    # --------------------------
    def set_button_style(self, button, state):
        def auto_setStyleSheet(button,backgroundColor:str, color:str,hover_backgroundColor:str,pressed_color="#e3e9eb"):
            button.setStyleSheet("""
                QPushButton {
                    background-color: """ + backgroundColor + """;
                    color: """ + color + """;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: """ + hover_backgroundColor +""";
                }
                QPushButton:pressed{
                    border: 2px solid """ + pressed_color + """;
                }
            """)
        button.setEnabled(True)
        match state:
            case "idle":
                auto_setStyleSheet(button,backgroundColor="#455A64",color="white",hover_backgroundColor="#adb5bd",pressed_color="#e3e9eb")
            case "primary":
                auto_setStyleSheet(button,backgroundColor="#0d6efd",color="white",hover_backgroundColor="#0055ff",pressed_color="#98c1fe")
            case "secondary":
                auto_setStyleSheet(button,backgroundColor="#6C757D",color="white",hover_backgroundColor="#5c636a",pressed_color="#c0c4c8")
            case "success":
                auto_setStyleSheet(button,backgroundColor="#198754",color="white",hover_backgroundColor="#157347",pressed_color="#9dccb6")
            case "danger":
                auto_setStyleSheet(button,backgroundColor="#DC3545",color="white",hover_backgroundColor="#bb2d3b",pressed_color="#f0a9b0")
            case "warning":
                auto_setStyleSheet(button,backgroundColor="#ffc107",color="black",hover_backgroundColor="#ffca2c",pressed_color="#ecd182")
            case "light":
                auto_setStyleSheet(button,backgroundColor="#f8f9fa",color="black",hover_backgroundColor="#f9fafb",pressed_color="#e9e9ea")
            case "stop":
                button.setStyleSheet("background-color: #E53935; color: white;")
            case "disabled":
                button.setStyleSheet("background-color: #B0BEC5; color: black; border: none; padding: 10px 20px; border-radius: 5px;")
                button.setEnabled(False)

    # --------------------------
    #   Datos tomados a mano
    # --------------------------
    def get_manual_data(self) -> dict:
        def parse_float(val):
            try:
                return float(val)
            except ValueError:
                return 0.0

        return {
            "RPM": parse_float(self.rpmEntry.text()),
            "I_disp": parse_float(self.iDispEntry.text())
        }