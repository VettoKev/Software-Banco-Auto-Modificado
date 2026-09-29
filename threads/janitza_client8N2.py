from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QThread
from pymodbus.client import ModbusSerialClient as ModbusClient
import time
import struct

class JanitzaClient8N2(QObject):
    janitzaDataReady = pyqtSignal(dict)

    def __init__(self,variables, COM_PORT = "COM4", poll_interval = 200, device_id = 40):
        super().__init__()
        self.poll_interval = poll_interval
        self.client = ModbusClient(port=COM_PORT, baudrate=19200, parity="N",stopbits=2,timeout=0.1)
        self.device_id = device_id
        if self.client.connect():
            print("Conectado a la red 8N2 (Janitza) por "+ COM_PORT)
        self.j_vars = []
        for var in variables:
            if var["slave"] == "Janitza":
                self.j_vars.append(var["label"])
    
    def start(self):
        self.timer = QTimer()
        self.timer.setInterval(self.poll_interval)
        self.timer.timeout.connect(self.getDataJanitza)
        self.timer.start(self.poll_interval)

    def stop(self):
        self.timer.stop()
    
    def getDataJanitza(self):
        try:
            lecturas = {}
            def decode_float32_janitza(reg_lo, reg_hi):
                """
                UMG503: float32 con swap de palabras y de bytes en cada palabra.
                Entrada: dos registros Modbus (16-bit) en el orden que los entrega pymodbus.
                reg_lo = primer registro leído (addr), reg_hi = segundo registro (addr+1)
                Salida: float32 correcto.
                Transformación de bytes: (HiWord,LoWord) y dentro de cada word [H,L] -> [L,H]
                [EB 9A] [6B 41]  ->  [41 6B 9A EB]
                """
                b0 = reg_hi & 0xFF          # low byte of high word
                b1 = (reg_hi >> 8) & 0xFF   # high byte of high word
                b2 = reg_lo & 0xFF          # low byte of low word
                b3 = (reg_lo >> 8) & 0xFF   # high byte of low word
                raw = bytes([b0, b1, b2, b3])
                return struct.unpack('>f', raw)[0]
            
            data_adress = [1012, 1000, 1036, 1072,1084] # Trios de datos : V, I. Pot, cos(phi) y frec
            COUNT = 6         # 3 floats -> 6 registros
            var_set = 0

            for adress in data_adress:
                rr = self.client.read_holding_registers(address=adress, count=COUNT,device_id=self.device_id)
                regs = rr.registers  # p.ej. [0xEB9A, 0x6B41, 0x5B20, 0x6E41, 0xC0B5, 0x6F41]
                for i in range(0, COUNT, 2):
                    key = self.j_vars[int(i/2+3*var_set)]
                    lecturas[key] = round(decode_float32_janitza(regs[i], regs[i+1]),2)
                var_set += 1
            self.janitzaDataReady.emit(lecturas)
        except:
            pass