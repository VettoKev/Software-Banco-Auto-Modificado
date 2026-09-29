from PyQt6.QtWidgets import QApplication
from GUI.main_window import MainWindow

import sys

def main(variables):
    app = QApplication([])

    window = MainWindow(variables)
    window.show()

    sys.exit(app.exec())

variables = [
        {"label": "Pe", "unit": "mca", "slave": 4},
        {"label": "Ps", "unit": "mca", "slave": 6},
        {"label": "Ps-Pe", "unit": "mca", "slave": 8},
        {"label": "T_amb", "unit": "°C", "slave": 5},
        {"label": "T_H2O", "unit": "°C", "slave": 7},
        {"label": "Caudal", "unit": "L/h", "slave": 2},
        {"label": "V1", "unit": "V", "slave": "Janitza"},
        {"label": "V2", "unit": "V", "slave": "Janitza"},
        {"label": "V3", "unit": "V", "slave": "Janitza"},
        {"label": "I1", "unit": "A", "slave": "Janitza"},
        {"label": "I2", "unit": "A", "slave": "Janitza"},
        {"label": "I3", "unit": "A", "slave": "Janitza"},
        {"label": "Pot1", "unit": "W", "slave": "Janitza"},
        {"label": "Pot2", "unit": "W", "slave": "Janitza"},
        {"label": "Pot3", "unit": "W", "slave": "Janitza"},
        {"label": "Fact P1", "unit": "-", "slave": "Janitza"},
        {"label": "Fact P2", "unit": "-", "slave": "Janitza"},
        {"label": "Fact P3", "unit": "-", "slave": "Janitza"},
        {"label": "f1", "unit": "Hz", "slave": "Janitza"},
        {"label": "f2", "unit": "Hz", "slave": "Janitza"},
        {"label": "f3", "unit": "Hz", "slave": "Janitza"},
        {"label": "U_Cap", "unit": "V", "slave": 10},
        {"label": "U_BA", "unit": "V", "slave": 9},
        ]

if __name__ == "__main__":
    main(variables)