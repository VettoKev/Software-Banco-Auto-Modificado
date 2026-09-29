from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QThread
from pymodbus.client import ModbusSerialClient as ModbusClient
from datetime import datetime

class ModbusClient8N1(QObject):
    new_data = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self,variables, COM_port = "COM3", poll_interval=200):
        super().__init__()
        self.poll_interval = poll_interval
        self.client = ModbusClient(port=COM_port, baudrate=19200, parity="N",stopbits=1,timeout=0.1)
        self.PLC_Adress = 15
        self.frec_50Hz = True
        self.isAuto = False
        if self.client.connect():
            print("Conectado a la red Modbus 8N1 (Novus) por puerto "+ COM_port)
        else:
            print(f"Error en conexion con {COM_port} desde modbus_client8N1")
        self.Caudalimetro = 2
        self.variables_N1500 = {}
        self.variablesToki = {}
        for _, var in enumerate(variables):
            slave_id = var["slave"]
            key = var["label"]
            if isinstance(slave_id, int):
                if key == "Caudal":
                    self.variables_N1500[key] = self.Caudalimetro
                elif key == "U_BA" or key == "U_Cap":
                    self.variablesToki[key] = slave_id
                else:
                    self.variables_N1500[key] = slave_id
        print(self.variablesToki)

    def start(self):
        self.timer = QTimer()
        self.timer.setInterval(self.poll_interval)
        self.timer.timeout.connect(self.poll_N1500)
        self.timer.start(200)

    def stop(self):
        self.timer.stop()

    def auto_toggle(self, cond:int):
        cond = bool(cond)
        if cond:
            print("Pasa a auto desde client 8N1")
            if self.isAuto:
                return
            del self.variables_N1500["Caudal"]
            self.isAuto = True
        else:
            print("pasa a manual desde client 8N1")
            if not self.isAuto:
                return
            self.variables_N1500["Caudal"] = self.Caudalimetro
            self.isAuto = False

    def poll_N1500(self):
        try:
            lecturas = {}
            REGISTRO_DISPLAY = 4 # 0x0004: valor que muestra el display
            def to_int16_signed(value):
                return value - 65536 if value > 32767 else value
            
            for key, value in self.variables_N1500.items():
                if key == "Caudal":
                    DECIMALES = 0
                else:
                    DECIMALES = 2        # Ajustar según configuración del N1500
                # key van a ser los nombres de las variables a leer y value el slave_id
                result = self.client.read_holding_registers(address=REGISTRO_DISPLAY, count=1, device_id=value)
                raw = result.registers[0]
                signed_val = to_int16_signed(raw)
                valor = signed_val / (10 ** DECIMALES)
                lecturas[key]=valor
            for key, value in self.variablesToki.items():
                result = self.client.read_holding_registers(address=16384,count=1,device_id=value)
                raw = result.registers[0]
                valor = raw/10
                lecturas[key] = valor
                # print(f"{key}: res={result} - raw={raw}")
            lecturas["Horario"] = datetime.now().strftime("%H:%M:%S")
            self.new_data.emit(lecturas)
        except Exception as e:
            # self.error.emit(e)
            pass

    def change_frec(self):
        if self.frec_50Hz:
            self.frec_50Hz = False
        else:
            self.frec_50Hz = True
    
    def change_caudalimetro(self, caudalimetroID: int):
        self.Caudalimetro = caudalimetroID
        self.variables_N1500["Caudal"] = caudalimetroID
        print(f"Cambio a Caudalimetro {self.Caudalimetro}")

    @pyqtSlot(dict)
    def handleCommand(self,command_dict:dict):
        sequence = command_dict.get("sequence", [])
        # Func para no andar tipeando de mas para cambiar el estado de las bobinas del PLC:
        def coil_state(self,coil_number,state):
            coil_number = int(str(coil_number),8)
            coil_number = coil_number + 2048 # Transforma a la numercacion del PLC (de octal a decimal y le suma 2048)
            self.client.write_coil(address=coil_number, value=bool(state), device_id=self.PLC_Adress)
        
        for step in sequence:
            coils = step.get("coils", {})
            delay = step.get("delay", 0)
            for coil, state in coils.items():
                    if coil == 0 and not self.frec_50Hz:
                        coil_state(self,1,state)
                        continue
                    coil_state(self,coil,state)
            if delay > 0:
                QThread.msleep(int(delay*1000))