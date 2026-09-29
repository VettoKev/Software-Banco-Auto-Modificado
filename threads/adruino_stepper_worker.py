# arduino_stepper_worker.py
import serial
import time
import threading
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer

START = 0xAA
END = 0x55

# Commands (mirror Arduino)
CMD_STEP_ENABLE      = 0x01
CMD_HOMING_REQUEST   = 0x02
CMD_SET_TARGET_FLOW  = 0x03
CMD_REQ_HOMING_LIMIT = 0x04

CMD_STATUS_PACKET    = 0x10
CMD_HOMING_LIMITS    = 0x11

ACK_MASK = 0x80

def crc8(data: bytes) -> int:
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc

def pack_frame(cmd: int, seq: int, payload: bytes) -> bytes:
    header = bytes([START, cmd & 0xFF, seq & 0xFF, len(payload)])
    body = header[1:] + payload  # cmd, seq, len + payload
    c = crc8(body)
    return header + payload + bytes([c, END])

class ArduinoStepperWorker(QObject):
    statusReceived = pyqtSignal(int, int, int, int)  # currentFlow, targetFlow, state, enabled
    homingLimitsReceived = pyqtSignal(int, int)      # minFlow, maxFlow
    ackReceived = pyqtSignal(int, int, bytes)        # ackCmd, seq, payload
    Qack = pyqtSignal(dict)
    log = pyqtSignal(str)

    def __init__(self, port:str ="COM9", baud: int = 115200, poll_interval_ms: int = 50):
        super().__init__()
        self.poll_interval_ms = poll_interval_ms
        self.running = False
        self.enabledAuto = False
        try:
            self.ser = serial.Serial(port, baud, timeout=0.1)
            # self.log.emit(f"Opened {port} at {baud}")
            print(f"Opened {port} at {baud}")
        except Exception as e:
            # self.log.emit(f"Failed to open serial {port}: {e}")
            print((f"Failed to open serial {port}: {e}"))

        # decoding state
        self._rx_state = 0
        self._rx_cmd = 0
        self._rx_seq = 0
        self._rx_len = 0
        self._rx_buf = bytearray()

        # seq for outgoing frames
        self._tx_seq = 0

        # ack wait tracking
        self._waiting_ack = {}  # seq -> dict {cmd, payload, tries, last_send_time, event}

    # ---------- public API slots ----------
    @pyqtSlot()
    def start(self):
        self.running = True
        self._timer = QTimer()
        self._timer.setInterval(self.poll_interval_ms)
        self._timer.timeout.connect(self._loop_once)
        self._timer.start()

    @pyqtSlot()
    def stop(self):
        self.running = False
        try:
            if hasattr(self, "_timer"):
                self._timer.stop()
        except Exception:
            pass
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.log.emit("Serial closed")

    # ---------- high-level commands ----------
    def _next_seq(self) -> int:
        self._tx_seq = (self._tx_seq + 1) & 0xFF
        return self._tx_seq

    def _send_and_wait_ack(self, cmd: int, payload: bytes, timeout: float = 0.6, retries: int = 3) -> bool:
        seq = self._next_seq()
        frame = pack_frame(cmd, seq, payload)
        entry = {"cmd": cmd, "payload": payload, "tries": 0, "last": 0, "seq": seq, "ack": None, "timeout": timeout, "retries": retries}
        self._waiting_ack[seq] = entry

        # send immediately
        self._transmit_entry(entry)
        # Wait by polling the entry ack in _loop_once (non-blocking) — simply return when ack found or tries exhausted
        start = time.time()
        while time.time() - start < (timeout * retries + 0.5):
            if entry["ack"] is not None:
                return True
            time.sleep(0.01)
        return False

    def _transmit_entry(self, entry):
        if not self.ser or not self.ser.is_open:
            return
        now = time.time()
        if entry["tries"] >= entry["retries"]:
            return
        # throttle retransmit: respect last send
        if now - entry["last"] < 0.05 and entry["tries"] > 0:  # small spacing after first
            return
        frame = pack_frame(entry["cmd"], entry["seq"], entry["payload"])
        try:
            self.ser.write(frame)
            entry["last"] = now
            entry["tries"] += 1
            self.log.emit(f"TX cmd=0x{entry['cmd']:02X} seq={entry['seq']} try={entry['tries']}")
        except Exception as e:
            self.log.emit(f"Serial write error: {e}")

    # Command wrappers (slots)
    @pyqtSlot(int)
    def set_stepper_enable(self, enable: int):
        payload = bytes([1 if enable else 0])
        self.log.emit(f"Enable cmd {enable}")
        # print(f"Enable cmd {enable}")
        _ = self._send_and_wait_ack(CMD_STEP_ENABLE, payload)
        # self.log.emit(f"STEP_ENABLE ack got: {success}")
        if self.enabledAuto is True:
            self.enabledAuto = False
        else:
            self.enabledAuto = True

    @pyqtSlot()
    def request_homing(self):
        payload = b""
        success = self._send_and_wait_ack(CMD_HOMING_REQUEST, payload)
        # self.log.emit(f"HOMING request ack: {success}")
        if success:
            self.request_homing_limits()

    @pyqtSlot(int)
    def set_target_flow(self, target: int):
        # target as uint16
        payload = bytes([(target >> 8) & 0xFF, target & 0xFF])
        _ = self._send_and_wait_ack(CMD_SET_TARGET_FLOW, payload)
        # self.log.emit(f"SET TARGET ack: {success}")

    @pyqtSlot()
    def request_homing_limits(self):
        payload = b""
        _ = self._send_and_wait_ack(CMD_REQ_HOMING_LIMIT, payload)
        # self.log.emit(f"REQ HOMING LIMITS ack: {success}")

    # ---------- read / decode / process ----------
    def _loop_once(self):
        # print("entra en start")
        # read bytes
        try:
            while self.ser.in_waiting:
                b = self.ser.read(1)
                if not b:
                    break
                self._process_rx_byte(b[0])
        except Exception as e:
            self.log.emit(f"Serial read error: {e}")
            return

        # manage retransmits for waiting ack entries
        to_delete = []
        for seq, entry in list(self._waiting_ack.items()):
            if entry["ack"] is not None:
                # confirmed ack, emit signal and remove
                self.ackReceived.emit(entry["cmd"], seq, entry["ack"])
                to_delete.append(seq)
            else:
                # not acked yet; maybe retransmit if timeout passed
                if time.time() - entry["last"] > entry["timeout"]:
                    if entry["tries"] < entry["retries"]:
                        self._transmit_entry(entry)
                    else:
                        # give up
                        self.log.emit(f"Giving up seq={seq} cmd=0x{entry['cmd']:02X}")
                        to_delete.append(seq)
        for seq in to_delete:
            del self._waiting_ack[seq]

    def _process_rx_byte(self, b: int):
        # decoder states similar to Arduino
        if self._rx_state == 0:  # WAIT START
            if b == START:
                self._rx_state = 1
                self._rx_buf = bytearray()
            return
        if self._rx_state == 1:  # CMD
            self._rx_cmd = b
            self._rx_state = 2
            return
        if self._rx_state == 2:  # SEQ
            self._rx_seq = b
            self._rx_state = 3
            return
        if self._rx_state == 3:  # LEN
            self._rx_len = b
            self._rx_buf = bytearray()
            if self._rx_len == 0:
                self._rx_state = 5  # CRC
            else:
                self._rx_state = 4
            return
        if self._rx_state == 4:  # PAYLOAD
            self._rx_buf.append(b)
            if len(self._rx_buf) >= self._rx_len:
                self._rx_state = 5
            return
        if self._rx_state == 5:  # CRC
            rxcrc = b
            # validate CRC
            body = bytes([self._rx_cmd, self._rx_seq, self._rx_len]) + bytes(self._rx_buf)
            calc = crc8(body)
            if calc != rxcrc:
                # CRC fail: drop frame
                self._rx_state = 0
                return
            self._rx_state = 6
            return
        if self._rx_state == 6:  # END
            if b == END:
                # full frame received and validated
                self._process_frame(self._rx_cmd, self._rx_seq, bytes(self._rx_buf))
            # reset
            self._rx_state = 0

    def _process_frame(self, cmd: int, seq: int, payload: bytes):
        if cmd == CMD_STATUS_PACKET:
            if len(payload) >= 6:
                curr = (payload[0] << 8) | payload[1]
                tgt  = (payload[2] << 8) | payload[3]
                state = payload[4]
                enabled = payload[5]
                if self.enabledAuto is True:
                    new_data = {}
                    new_data["Caudal"] = curr
                    self.Qack.emit(new_data)
                # self.statusReceived.emit(curr, tgt, state, enabled)
                # print(f"Current target {tgt}, state: {state}, enabled: {enabled}")
        elif cmd == CMD_HOMING_LIMITS:
            if len(payload) >= 4:
                mn = (payload[0] << 8) | payload[1]
                mx = (payload[2] << 8) | payload[3]
                self.homingLimitsReceived.emit(mn, mx)
        else:
            # ACK or NACK: commands >= 0x80
            if cmd & ACK_MASK:
                origCmd = cmd & (~ACK_MASK)
                # find waiting entry by seq
                e = self._waiting_ack.get(seq)
                if e is not None:
                    # store ack payload
                    e["ack"] = payload
                    # ack will be handled in _loop_once
                    self.log.emit(f"ACK for seq {seq} cmd 0x{origCmd:02X}")
            else:
                # Unexpected unsolicted frame - ignore or handle
                self.log.emit(f"RX unsolicited cmd 0x{cmd:02X}")

# ---- end of worker class ----
