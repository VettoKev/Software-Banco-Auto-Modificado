import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
import pandas as pd
import numpy as np

class AdquiridoPlot(QWidget):
    def __init__(self, title = "Insert Title", chosen_vars = ["Pe","Ps","Ps-Pe"], y_label = "y_label"):
        super().__init__()
        pg.setConfigOption("background", (240,240,240))
        pg.setConfigOption("foreground", "k")
        pg.setConfigOption("antialias", True)
        color_list = ["r", "b", "g"]

        self.chosen_vars = chosen_vars
        layout = QVBoxLayout(self)

        self.plotWidget = pg.PlotWidget(title=title,antialias=True)
        self.plotWidget.getPlotItem().getViewBox().setDefaultPadding(0.05)
        self.plotWidget.setLabel("left",y_label)
        self.plotWidget.setLabel("bottom","Caudal", units="L/h")
        legend = self.plotWidget.addLegend()
        legend.anchor((0,0),(0,0))
        self.plotWidget.showGrid(x=True,y=True)
        layout.addWidget(self.plotWidget)

        # Crea las curvas:
        self.curves = {}
        self.labels = {}
        self.std = {}
        for i, var in enumerate(chosen_vars):
            self.curves[var] = self.plotWidget.plot(
                pen=pg.mkPen(color_list[i],width=2),
                symbol='o',
                symbolBrush=color_list[i],
                name=var
            )
            self.labels[var] = pg.TextItem("", anchor=(0, 1.0),color='k')
            self.plotWidget.addItem(self.labels[var])
            self.std[var] = pg.ErrorBarItem(beam=0.5)
            self.plotWidget.addItem(self.std[var])
    
    def update_adquirido(self, data:pd.DataFrame):
        data = data.sort_values(by="Caudal",ascending=False)
        caudal_data = data["Caudal"].to_list()
        for var in self.chosen_vars:
            yData = data[var].to_list()
            self.curves[var].setData(caudal_data,yData,name=var)
            self.labels[var].setText(text=f"{caudal_data[-1]:.1f}; {yData[-1]:.1f}")
            self.labels[var].setPos(caudal_data[-1],yData[-1])
    
    def update_error_bars(self, data_mean:pd.DataFrame, data_std:pd.DataFrame):
        data_mean = data_mean.sort_values(by="Caudal",ascending=False)
        data_std = data_std.sort_values(by="Caudal",ascending=False)
        caudal_mean = data_mean["Caudal"].to_numpy()
        caudal_std = data_std["Caudal"].to_numpy()
        for var in self.chosen_vars:
            yMean = data_mean[var].to_numpy()
            yStd = data_std[var].to_numpy()
            self.std[var].setData(
                x = caudal_mean,
                y = yMean,
                height = yStd,
                width = caudal_std)
    
    def borrar_todo(self):
        for var in self.chosen_vars:
            self.curves[var].setData([],[])
            self.labels[var].setText("")

    def agregar_comp(self,compDict:dict,keyVar:str):
        color_list = ["m","c","y"]
        self.compCurves = {}
        for i,ensayo in enumerate(list(compDict.keys())):
            caudal = compDict[ensayo]["Caudal"]
            y_var = compDict[ensayo][keyVar]
            self.compCurves[ensayo] = self.plotWidget.plot(
                pen=pg.mkPen(color_list[i],width=2),
                symbol='o',
                symbolBrush=color_list[i],
                name=ensayo
            )
            self.compCurves[ensayo].setData(caudal,y_var)
    
    def borrar_todos_comp(self):
        for ensayo in self.compCurves.keys():
            self.plotWidget.removeItem(self.compCurves[ensayo])
        #     self.compCurves[ensayo].setData([],[])
        self.compCurves.clear()
    
    def borrar_n_comp(self,ensayos:list):
        for ensayo in ensayos:
            self.plotWidget.removeItem(self.compCurves[ensayo])
            del self.compCurves[ensayo]

