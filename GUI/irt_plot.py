import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout

class IRTPlot(QWidget):
    def __init__(self, title = "insert title", chosen_vars = ["Ps-Pe"], yLabel = "Presion [mca]"):
        super().__init__()
        pg.setConfigOption("background", (240,240,240))
        pg.setConfigOption("foreground", "k")

        color_list = ["r", "b", "g"]
        self.chosen_vars = chosen_vars
        layout = QVBoxLayout(self)

        self.plotWidget = pg.PlotWidget(title=title)
        self.plotWidget.setLabel("left",yLabel)
        self.plotWidget.setLabel("bottom", "Samples")
        self.plotWidget.addLegend()
        self.plotWidget.showGrid(x=True,y=True)
        layout.addWidget(self.plotWidget)

        # Crea las curvas:
        self.curves = {}
        for i,var in enumerate(chosen_vars):
            self.curves[var] = self.plotWidget.plot(pen=pg.mkPen(color_list[i],width=2),name=var)
        
    def update_buffer(self,buffer):
        for var in self.chosen_vars:
            data = buffer.get(var, [])
            self.curves[var].setData(data, name=var)