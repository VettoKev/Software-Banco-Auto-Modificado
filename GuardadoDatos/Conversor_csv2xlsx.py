import pandas as pd
import os
import json

from GuardadoDatos.conversor_csv2xlsx_Inverter import csv2xlsx_inverter
from GuardadoDatos.conversor_csv2xlsx_Mono import csv2xlsx_Mono
from GuardadoDatos.conversor_csv2xlsx_MonoVar import csv2xlsx_MonoVar
from GuardadoDatos.conversor_csv2xlsx_Trifasico import csv2xlsx_Trifasico
from GuardadoDatos.conversor_csv2xlsx_PerdidaDeCarga import csv2xlsx_PerdidaDeCarga
from GuardadoDatos.conversor_csv2xlsx_Vacio import csv2xlsx_Vacio

def csv2xlsx(csvFile, modeloBomba = None, tipoEnsayo = "Curva Caracteristica", metadata:dict = None):
    print(f"Desde el csv2xlsx, bomba: {modeloBomba}, tipo de ensayo: {tipoEnsayo}")
    multietapa_lista = ["Multietapa P60 - TANGO", "Multietapa P60 - INTELIG", "Multietapa P90 - TANGO","Multietapa P90 - INTELIG"]

    filePath = os.path.join("ArchivosAuxiliares","bombas.json")
    with open(filePath,"r") as f:
        bombasData = json.load(f)
    datosMotor = None
    match tipoEnsayo:
        case "Curva Caracteristica":
            if modeloBomba is None:
                carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Ensayos a Pasar\\"
            elif modeloBomba in multietapa_lista:
                carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Bombas\\Multietapa (proyecto)\\Ensayos\\"
            elif modeloBomba == "Inverter":
                carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\I+D\\Inverter\\Ensayos\\"
            else:
                carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Bombas\\" + modeloBomba + "\\Ensayos"
                if os.path.isdir(carpeta_excel):
                    carpeta_excel = carpeta_excel + "\\"
                else:
                    carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Bombas\\" + modeloBomba + "\\Curvas caracteristicas\\"
                if not os.path.isdir(carpeta_excel):
                    print(f"LA CARPETA con path: {carpeta_excel} NO EXISTE")
        case "Perdida de Carga":
            carpeta_excel =  "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Validacion de Componentes\\"
        case "Regimen Termico" | "Vacio":
            if modeloBomba is None:
                carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Ensayos a Pasar\\"
            elif modeloBomba in multietapa_lista:
                carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Bombas\\Multietapa (proyecto)\\"+tipoEnsayo+"\\"
            elif modeloBomba == "Inverter":
                carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\I+D\\Inverter\\Regimen Térmico\\"
            else:
                carpeta_excel = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Bombas\\" + modeloBomba + "\\"+tipoEnsayo+"\\"
    
    if modeloBomba:
        datosMotor = bombasData.get(modeloBomba,{})
        if not datosMotor:
            print("Se omiten datos del motor (no se cargaron)")
    if metadata:
        datosMotor = metadata
    title = os.path.splitext(os.path.basename(csvFile))[0]

    outputFile = carpeta_excel + title + ".xlsx"
    print(f"outputFile: {outputFile}")
    is_Monofasico = False

    df = pd.read_csv(csvFile, sep=";")
    dimensions = df.shape
    last_row = dimensions[0]-1
    monofasico_cond = df.iloc[last_row,0]
    df.drop(last_row, inplace=True)

    df = df.sort_values(by="Caudal",ascending=False)

    # Chequea que el ultimo valor de caudal sea positivo:
    last_row_index = df.iloc[-1].name
    if df.loc[last_row_index,"Caudal"] < 0:
        print("Entra a coreregir caudal negativo")
        df.loc[last_row_index,"Caudal"] = 0
    df_temporal = df.sort_values(by="Horario")

    if monofasico_cond == 1:
        is_Monofasico = True
    elif monofasico_cond == 0:
        is_Monofasico = False
    else:
        print("Error, no detecta si es mono o trifasico")
    
    match tipoEnsayo:
        case "Curva Caracteristica":
            if modeloBomba == "Inverter":
                csv2xlsx_inverter(outputFile,title,df,df_temporal)
            elif is_Monofasico and (not datosMotor or not datosMotor["Variador"]):
                csv2xlsx_Mono(outputFile,title,df,df_temporal,datosMotor,modeloBomba)
            elif is_Monofasico and datosMotor["Variador"]:
                csv2xlsx_MonoVar(outputFile,title,df,df_temporal,datosMotor,modeloBomba)
            else:
                csv2xlsx_Trifasico(outputFile,title,df,df_temporal,datosMotor)
        
        case "Perdida de Carga":
            csv2xlsx_PerdidaDeCarga(outputFile,title,df,df_temporal)
        case "Regimen Termico":
            print("Todavia falta hacer Regimen Termico")
        case "Vacio":
            csv2xlsx_Vacio(outputFile,title,df,df_temporal,datosMotor,modeloBomba)