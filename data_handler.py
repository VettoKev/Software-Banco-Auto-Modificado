from PyQt6.QtCore import QObject, pyqtSignal
from collections import deque
from datetime import date, datetime
import pandas as pd
import csv
import os
import numpy as np

from GuardadoDatos.Conversor_csv2xlsx import csv2xlsx
from GuardadoDatos.auto_manual2xlsx import DataFrame2xlsx

from db.db_manager import DatabaseManager
from db.repos import BombaRepository, EnsayoRepository, MedicionRepository
from db.field_map import normalize_overrides, normalize_df_data

import pandas as pd

class DataHandler(QObject):
    bombasList = pyqtSignal(list)
    dataUpdated = pyqtSignal(dict)
    bufferUpdated = pyqtSignal(dict)
    pointAcquired = pyqtSignal(pd.DataFrame)
    logMsg = pyqtSignal(str)
    stepAcq = pyqtSignal()
    stdAcquired = pyqtSignal(pd.DataFrame, pd.DataFrame)

    def __init__(self, variables, db : DatabaseManager, buffer_size = 100, windowSize = 20):
        super().__init__()
        self.metadata = {}
        self.variables = [v["label"] for v in variables]
        self._variables_dict = variables
        # Variables para el ensayo auto y semi-auto
        self.qualityWindow = {var: deque(maxlen=windowSize) for var in self.variables}
        self.lastQAcq = None
        self.targetQ = None
        self.toleranciaQ = 50
        self.stdDf = pd.DataFrame(columns=self.variables)
        self.fullPoints = pd.DataFrame(columns=self.variables)
        self.isAuto = True

        # Agrega Horario para el otro DF
        self.variables.insert(len(self.variables),"Horario")
        self.meanDf = pd.DataFrame(columns=self.variables)
        self.buffer = {var: deque(maxlen=buffer_size) for var in self.variables}
        self.all_data = {k: None for k in self.variables}
        self.history = pd.DataFrame(columns=self.variables)
        
        # Variables auxiliares:
        self.isMonofasico = True
        self.bomba = None
        self.tipoEnsayo = "Curva Caracteristica"

        # MySQL:
        self.db = db
        self.bomba_repo = BombaRepository(db)
        self.ensayo_repo = EnsayoRepository(db)
        self.medicion_repo = MedicionRepository(db)
        self._current_bomba = None
        self._data_select = None
        self._overrides = {}

    def load_bombas(self):
        bombas_list_aux = self.bomba_repo.get_all()
        self.bombas_list = [b.bomba for b in bombas_list_aux]
        # print(f"{self.bombas_list=}")
        self.bombasList.emit(self.bombas_list)
        self._bomba_map = {b.bomba: b for b in bombas_list_aux}
    
    def on_status_change(self, bombasList):
        print(f"{bombasList=}")

    def update_irt(self, new_data:dict):
        for key, value in new_data.items():
            self.all_data[key] = value
            self.buffer[key].append(value)
            if key == "Horario":
                continue
            else:
                self.qualityWindow[key].append(value)
        self.dataUpdated.emit(self.all_data.copy())
        self.bufferUpdated.emit(self.buffer.copy())
        if "Caudal" in new_data.keys():
            self.SS_check_acq()

    def update_target(self, newTarget:float):
        self.targetQ = newTarget
    
    def semi_auto_toggle(self):
        if self.isAuto is True:
            self.isAuto = False
        else:
            self.isAuto = True
    
    def SS_check_acq(self): # chequea Steady State y si todos los puntos estan en el rango, toma los datos 
        target = self.targetQ 
        if self.lastQAcq == target or target is None:
            return
        caudal = self.qualityWindow["Caudal"]
        if target == 0:
            deltaP = list(self.qualityWindow["Ps-Pe"])
            minP = min(deltaP)
            maxP = max(deltaP)
            if not (maxP-minP)<0.1:
                return
            if not all(q==0 for q in caudal):
                return

        Qlow = target - self.toleranciaQ
        Qhigh = target + self.toleranciaQ

        if not all(Qlow <= q <= Qhigh for q in caudal):
            return

        self.lastQAcq = target
        pointDf = pd.DataFrame(self.qualityWindow)

        meanDf = pd.DataFrame(pointDf.mean().round(2)).T
        meanDf["Horario"] = datetime.now().strftime("%H:%M:%S")
        stdDf = pd.DataFrame(pointDf.std().round(2)).T

        self.meanDf = pd.concat([self.meanDf,meanDf], ignore_index=True)
        self.stdDf = pd.concat([self.stdDf,stdDf], ignore_index=True)
        self.fullPoints = pd.concat([self.fullPoints,pointDf], ignore_index=True)
        self.pointAcquired.emit(self.meanDf.copy())
        self.stdAcquired.emit(self.meanDf.copy(), self.stdDf.copy())
        self.logMsg.emit("Punto adquirido a "+str(meanDf["Caudal"])+" L/h")
        if self.isAuto:
            self.stepAcq.emit()

    def adquirir_datos(self, manual_data: dict = None):
        new_data = {}
        for var, dq in self.buffer.items():
            if manual_data and var in manual_data:
                new_data[var] = manual_data[var]
            elif dq:
                new_data[var] = dq[-1]
            else:
                new_data[var] = 0.0
        self.history = pd.concat([self.history,pd.DataFrame(new_data, index=[0])], ignore_index = True)
        # self.history = self.history.sort_values(by="Caudal",ascending=False)
        self.pointAcquired.emit(self.history.copy())
        self.logMsg.emit("Tomar datos a "+str(new_data["Caudal"])+" L/h")
    
    def borrar_ultimo(self):
        self.logMsg.emit("Borrar ultimo: Q="+str(self.history["Caudal"].index[-1]))
        self.history = self.history.drop(self.history.index[-1])
        self.pointAcquired.emit(self.history.copy())

    def borrar_todo(self):
        self.history = pd.DataFrame(columns=self.variables)
        self.logMsg.emit("Borrar Todo")
        # self.pointAcquired.emit(self.history.copy())

    def change_bomba(self, bomba:str):
        print(f"Cambio a {bomba} desde Data Handler")
        self.bomba = bomba
    
    def chage_tipo_ensayo(self,tipoEnsayo:str):
        print(f"Cambio a tipo de ensayo: {tipoEnsayo} desde Data Handler")
        self.tipoEnsayo = tipoEnsayo

    def changeMonofasico(self,isMonofasico):
        print(f"desde Datahandler, isMonofasico = {isMonofasico}")
        self.isMonofasico = isMonofasico

    def update_metadata(self,metadata:dict):
        self.metadata = metadata

    def change_bomba(self, bomba_name: str):
        self.logMsg.emit(f"Cambio a {bomba_name} desde Data Handler")
        self.bomba = bomba_name
        self._current_bomba = self._bomba_map.get(bomba_name)
        if self._current_bomba:
            self._data_select = self.bomba_repo.get_data_select(self._current_bomba)
            for var, value in vars(self._data_select).items():   
                print(f"{var=} {value=}")

    def update_metadata(self, metadata: dict):
        self.metadata = metadata
        self._overrides.update(metadata)    # metadata feeds into overrides at save time

    def _save_to_db(self, df: pd.DataFrame, num_ensayo: str):
        if self._current_bomba is None or self._data_select is None:
            self.logMsg.emit("Error: no hay bomba seleccionada, no se guardó en DB")
            return

        # num_ensayo is passed in from guardar_datos/guardar_datos_auto
        # since they already compute it
        raw_overrides = {**self._overrides, "num_ensayo": num_ensayo}
        overrides = normalize_overrides(raw_overrides)

        df = normalize_df_data(df)

        try:
            ensayo_id = self.ensayo_repo.create(self._current_bomba, overrides)
            for _, row in df.iterrows():
                caudal = row.get("Caudal", 0.0)
                mediciones = [
                    {"variable": var, "valor": row.get(var, 0.0), "unit": None}
                    for var in self.variables
                    if var not in ("Caudal", "Horario")
                    and (getattr(self._data_select, var, False) or var == "Ps-Pe")
                ]
                self.medicion_repo.save_punto(ensayo_id, caudal, mediciones)
            self.logMsg.emit(f"Guardado en DB: ensayo {num_ensayo}")
        except Exception as e:
            self.logMsg.emit(f"Error guardando en DB: {e}")

    def guardar_datos(self):
        self.logMsg.emit("Guardando Datos")
        csvFileNames = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\lista_ensayos.csv"

        num_ensayo = self.getNumEnsayo()
        file_name = num_ensayo + ".csv"
        print(f"file_name desde el GUI: {file_name}")

        archivo = self.history.copy()
        new_index = len(archivo)
        archivo.loc[new_index] = pd.Series({archivo.columns[0]: self.isMonofasico})

        file_name_local = "C:\\Users\\Rowa Lab\\Documents\\archivos csv\\"+file_name
        file_name = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\datos_adquiridos\\"+file_name

        archivo.to_csv(file_name, index=False, sep=";")
        archivo.to_csv(file_name_local,index=False, sep=";")
        csv2xlsx(csvFile=file_name, modeloBomba=self.bomba, tipoEnsayo=self.tipoEnsayo, metadata=self.metadata)
        
        with open (csvFileNames, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([num_ensayo + ".csv"])
        self._save_to_db(self.history,num_ensayo)
        print("Hola Miguel")
        self.logMsg.emit("Data Saved")
        print("Data saved")

    def guardar_datos_auto(self):
        # self.meanDf.to_csv("test_mean.csv",index=False,sep=";")
        # self.stdDf.to_csv("test_std.csv",index=False,sep=";")
        # self.fullPoints.to_csv("test_full.csv",index=False,sep=";")
        self.logMsg.emit("Guardando Datos")
        fecha = date.today().strftime("%d%m%y")
        csvFileNames = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\lista_ensayos.csv"
        contents = []
        try:
            with open(csvFileNames, 'r', newline="") as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    contents.extend(row)
        except:
            print("No se pudo abrir el archivo csv con los nombres de ensayo")
            directory_local = "C:\\Users\\Rowa Lab\\Documents\\archivos csv"
            i_ensayo_local = 0
            for ensayo in os.listdir(directory_local):
                fecha_ensayo , _ = ensayo.split("-")
                if fecha_ensayo==fecha:
                    i_ensayo_local += 1
            last_ensayo = fecha + "-" +str(i_ensayo_local) + ".csv"
        
        print("Numerado Automatico de Ensayo")
        ensayo_index = 1
        last_ensayo = contents[-1][:-4]
        fecha_last, ensayo_num_last = last_ensayo.split("-")
        ensayo_num_last = int(ensayo_num_last)
        if fecha == fecha_last:
            ensayo_index = ensayo_num_last+1
        file_name = fecha+"-"+str(ensayo_index)+".csv"
        num_ensayo = fecha+"-"+str(ensayo_index)
        with open (csvFileNames, 'a', newline="") as f:
            writer = csv.writer(f)
            writer.writerow([file_name])
        print(f"file_name desde el GUI: {file_name}")
        archivoMean = self.meanDf.copy()
        new_index = len(archivoMean)
        archivoMean.loc[new_index] = pd.Series({archivoMean.columns[0]: self.isMonofasico})

        file_name_local = "C:\\Users\\Rowa Lab\\Documents\\archivos csv\\"+file_name
        file_name = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\datos_adquiridos\\"+file_name
        
        DataFrame2xlsx(df_mean=archivoMean,df_std=self.stdDf,numEnsayo=num_ensayo, modeloBomba=self.bomba, tipoEnsayo=self.tipoEnsayo,metadata=self.metadata)

        archivoMean.to_csv(file_name, index=False, sep=";")
        archivoMean.to_csv(file_name_local,index=False, sep=";")
        self.fullPoints.to_parquet("\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\datos_adquiridos\\"+num_ensayo+".parquet",index=False)
        self.fullPoints.to_parquet("C:\\Users\\Rowa Lab\\Documents\\archivos csv\\"+num_ensayo+".parquet",index=False)
        self.logMsg.emit("Data saved del auto")
    
    def getNumEnsayo(self):
        fecha = date.today().strftime("%d%m%y")
        csvFileNames = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\lista_ensayos.csv"
        contents = []
        try:
            with open(csvFileNames, 'r', newline="") as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    contents.extend(row)
            self.logMsg.emit("Numerado Automatico de Ensayo")
            print("Numerado Automatico de Ensayo")
            ensayo_index = 1
            last_ensayo = contents[-1][:-4]
            fecha_last, ensayo_num_last = last_ensayo.split("-")
            ensayo_num_last = int(ensayo_num_last)
            if fecha == fecha_last:
                ensayo_index = ensayo_num_last+1
            num_ensayo = fecha+"-"+str(ensayo_index)
        except:
            self.logMsg.emit("No se pudo abrir el archivo csv con los nombres de ensayo")
            print("No se pudo abrir el archivo csv con los nombres de ensayo")
            directory_local = "C:\\Users\\Rowa Lab\\Documents\\archivos csv"
            i_ensayo_local = 1
            for ensayo in os.listdir(directory_local):
                fecha_ensayo , _ = ensayo.split("-")
                if fecha_ensayo==fecha:
                    i_ensayo_local += 1
            num_ensayo = fecha + "-" +str(i_ensayo_local)
        
        self.logMsg.emit("Ensayo N°: "+num_ensayo)
        return num_ensayo
