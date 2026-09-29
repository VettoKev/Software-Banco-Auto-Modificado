import pandas as pd
import os
import json

from GuardadoDatos.conversor_csv2xlsx_Mono import df_auto2xlsx_mono

def DataFrame2xlsx(df_mean:pd.DataFrame, df_std:pd.DataFrame, numEnsayo:str, modeloBomba:str=None, tipoEnsayo:str=None, metadata:dict=None):
    print("")
    datosMotor = None
    multietapa_lista = ["Multietapa P60 - TANGO", "Multietapa P60 - INTELIG", "Multietapa P90 - TANGO","Multietapa P90 - INTELIG"]

    filePath = os.path.join("ArchivosAuxiliares","bombas.json")
    with open(filePath,"r") as f:
        bombasData = json.load(f)
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
            if not metadata:
                metadata={'Paquete': "", 'Motor': "", 'Caracol': '', 'Capa Nominal': '', 'Variador': [], 'Variador frec': [], 'BP Cables': "", 'BP Diam': "", 'BP PE': '', 'BA Diam': "", 'BA PE': '', 'Turbina': '', 'Diametro Turbina': '', 'Bobinado': 'STD', 'Control': 'NO'}
                print("Se crea metadata con parametros vacios")

    outputFile = carpeta_excel + numEnsayo + ".xlsx"
    print(f"outputFile: {outputFile}")
    is_Monofasico = False
    
    dimensions = df_mean.shape
    last_row = dimensions[0]-1
    monofasico_cond = df_mean.iloc[last_row,0]
    df_mean.drop(last_row, inplace=True)

    df_mean = df_mean.sort_values(by="Caudal",ascending=False)
    df_std = df_std.sort_values(by="Caudal",ascending=False)

    # Chequea que el ultimo valor de caudal sea positivo:
    last_row_index = df_mean.iloc[-1].name
    if df_mean.loc[last_row_index,"Caudal"] < 0:
        print("Entra a coreregir caudal negativo")
        df_mean.loc[last_row_index,"Caudal"] = 0
    # df_temporal = df_mean.sort_values(by="Horario")

    if monofasico_cond == 1:
        is_Monofasico = True
    elif monofasico_cond == 0:
        is_Monofasico = False
    else:
        print("Error, no detecta si es mono o trifasico")

    match tipoEnsayo:
        case "Curva Caracteristica":
            if modeloBomba == "Inverter":
                # csv2xlsx_inverter(outputFile,title,df,df_temporal)
                pass
            elif is_Monofasico and (not datosMotor or not datosMotor["Variador"]):
                df_auto2xlsx_mono(outputFile,title="",dfMean=df_mean,dfStd=df_std,metadata=metadata,modeloBomba=modeloBomba)
            elif is_Monofasico and datosMotor["Variador"]:
                # csv2xlsx_MonoVar(outputFile,title,df,df_temporal,datosMotor,modeloBomba)
                pass
            else:
                # csv2xlsx_Trifasico(outputFile,title,df,df_temporal,datosMotor)
                pass
        
        case "Perdida de Carga":
            # csv2xlsx_PerdidaDeCarga(outputFile,title,df,df_temporal)
            pass
        case "Regimen Termico":
            print("Todavia falta hacer Regimen Termico")
        case "Vacio":
            # csv2xlsx_Vacio(outputFile,title,df,df_temporal,datosMotor,modeloBomba)
            pass
