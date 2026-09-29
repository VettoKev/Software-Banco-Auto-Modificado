from PyQt6.QtWidgets import QLabel, QWidget, QGridLayout, QLineEdit
from PyQt6.QtCore import Qt
import math

class DataDisplay(QWidget):
    MANUAL_VARS = ["RPM", "I_disp"]

    def __init__(self, variables):
        super().__init__()

        self.variables = variables
        max_rows = 6
        n_cols = (math.ceil(len(self.variables)/max_rows))*3

        # Layout set
        layout = QGridLayout()
        self.setLayout(layout)

        self.vars = []
        self.entries = {}
        i_row = 0
        i_col = 0
        for i, cfg in enumerate(self.variables):
            i_col = 3*(i//6)
            i_row = i -6*(i//6)
            label = QLabel(parent=self, text= cfg["label"])
            label.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.vars.append(cfg["label"])
            layout.addWidget(label, i_row, i_col)
            # var = ttk.StringVar(value="0.0")
            # self.vars[cfg["label"]] = var
            # entry = ttk.Entry(self, textvariable=var,state="readonly",width=10).grid(row=i_row,column=i_col+1,padx=5,sticky="ew")
            entry = QLineEdit(self)
            entry.setText("0.0")
            
            # Si no es variable manual, se deja solo lectura
            if cfg["label"] not in self.MANUAL_VARS:
                entry.setReadOnly(True)

            layout.addWidget(entry, i_row, i_col+1)
            # ttk.Label(self, text=cfg["unit"]).grid(row=i_row, column=i_col+2, sticky='w',padx=5)
            self.entries[cfg["label"]] = entry

            label_units = QLabel(parent=self, text=cfg["unit"])
            layout.addWidget(label_units, i_row, i_col+2)
        
        for i in range(0,max_rows):
            layout.setRowStretch(i,1)

        for i in range(0,n_cols):
            layout.setColumnStretch(i,1)
    
    def update_data(self, data_dict:dict):
        for key, value in data_dict.items():
            if key in self.vars and key not in self.MANUAL_VARS:
                self.entries[key].setText(str(value))

    def get_manual_data(self) -> dict:
        """Devuelve los valores ingresados manualmente en pantalla."""
        manual_values = {}
        for var in self.MANUAL_VARS:
            if var in self.entries:
                try:
                    manual_values[var] = float(self.entries[var].text())
                except ValueError:
                    manual_values[var] = 0.0
        return manual_values           
