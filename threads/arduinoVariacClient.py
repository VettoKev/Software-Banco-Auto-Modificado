from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QThread, QTimer
import struct
import serial
import time

class arduinoVariac(QObject):
    # statusRecieved = pyqtSignal(float, float)
    logMessage =pyqtSignal(str)

    def __init__(self, COM_PORT = "COM8", baudrate = 115200,poll_interval_ms =20):
        super().__init__()
        try:
            self.serial = serial.Serial(port=COM_PORT, baudrate=baudrate, timeout=0.1)
            print(f"Conectado al arduino del Variac exitosamente por puerto {COM_PORT}")
        except:
            print("No se pudo conectar al arduino del Variac")
        self.running = False
        self.timer = None
        self.poll_interval_ms = poll_interval_ms

        self.lastTargetSent = None
        self.waitingACK = False
        self.lastSendTime = 0.0

    @pyqtSlot(float)
    def set_target_voltage(self, voltage):
        scaled = int(voltage*10)
        self.lastTargetSent = scaled
        self.send_target(scaled)

    def send_target(self, scaled_target:int):
        packet = struct.pack("<B B h B", 0xAA, 0x01, scaled_target, 0x55)
        self.serial.write(packet)
        self.lastSendTime = time.time()
        self.logMessage.emit(f"Sent Target: {scaled_target/10}")
        # print(f"Sent Target: {scaled_target/10}")

    # =======================================================
    # Background loop
    # =======================================================
    @pyqtSlot()
    def pollLoop(self):
        try:
            if not self.serial or not self.serial.is_open:
                return
            # check if there is at least 1 byte available
            if self.serial.in_waiting <= 0:
                pass
            else:
                # Attempt to read a frame as your original code did
                b = self.serial.read(1)
                if b != b'\xAA':
                    # If not sync byte, drop it (or attempt to resync)
                    return
                payload = self.serial.read(5)
                if len(payload) != 5:
                    return
                # unpack with little-endian signed shorts and a byte
                try:
                    _, target_raw, end = struct.unpack("<h h B", payload)
                except struct.error:
                    return
                if end != 0x55:
                    return
                # voltage = voltage_raw / 10.0
                target = target_raw / 10.0

                # If we were waiting for ack, check it
                if self.waitingACK and (int(target*10) == self.lastTargetSent):
                    self.logMessage.emit("Desde Arduino Stepper, target confirmed = "+str(target))
                    self.waitingACK = False

        except Exception as e:
            # never allow exceptions to bubble and stop the timer loop
            print(f"Poll error: {e}")
            self.stop()
            try:
                self.serial = serial.Serial(port=COM_PORT, baudrate=baudrate, timeout=0.1)
                print(f"Conectado al arduino del Variac exitosamente por puerto {COM_PORT}")
            except:
                print("No se pudo conectar al arduino del Variac")
            self.start()
            # pass

        # If waiting ack and timed out, retransmit (retry policy)
        if self.waitingACK:
            if time.time() - self.lastSendTime > 0.5:   # retry every 0.5s
                if self.lastTargetSent is not None:
                    self.send_target(self.lastTargetSent)

    def start(self):
        if self.running:
            return
        self.running = True

        self.timer = QTimer()
        self.timer.setInterval(self.poll_interval_ms)
        self.timer.timeout.connect(self.pollLoop)
        self.timer.start()

    # =======================================================
    # Read & decode status frame
    # =======================================================
    def read_status(self):
        if self.serial.read(1) != b'\xAA':
            return None

        payload = self.serial.read(5)
        if len(payload) != 5:
            return None

        voltage_raw, target_raw, end = struct.unpack("<h h B", payload)

        if end != 0x55:
            return None

        voltage = voltage_raw / 10.0
        target = target_raw / 10.0
        return voltage, target

    # =======================================================
    # Stop worker
    # =======================================================
    @pyqtSlot()
    def stop(self):
        self.running = False
        if self.timer and self.timer.isActive():
            self.timer.stop()
            print("Timer stop")
        try:
            if self.serial and self.serial.is_open:
                self.serial.close()
                print("Serial Close")
        except Exception as e:
            print(f"Serial close error: {e}")