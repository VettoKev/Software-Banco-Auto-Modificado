"""
Muchos ensayos no siguen el formato STD por lo que 
se deben cargar a mano el numero de fila en que esta cada variable

No es lo ideal pero como esto es algo que se deberia hacer una sola vez
decidi hacerlo de esta manera

Sepan disculpar

Pd: Si estas leyendo esto, puto el que lee
"""
import pandas as pd
import numpy as np
import os
import sys

from ingestion.template_map import normalize_variables_tabla

dir = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Bombas\\Tango 9\\Curvas caracteristicas\\060825-6.xlsx"

def extraer_datos_ensayo(path_excel: str, caso: int) -> pd.DataFrame:
    xls = pd.ExcelFile(path_excel)
    hoja = xls.sheet_names[1] #
    df_raw = pd.read_excel(path_excel,sheet_name=hoja)
    # print(df_raw)

    #Busca la primera fila tipo header 
    fila_header_idx = None
    for i in range(len(df_raw)):
        row = df_raw.iloc[i]
        if isinstance(df_raw.iloc[i,1],(int,float,np.number)) and isinstance(df_raw.iloc[i,2],(int,float,np.number)):
            fila_header_idx = i
            if not df_raw.isna().iloc[i,1] or not df_raw.isna().iloc[i,2]:
                # print(f"fila inicial de la tabla {fila_header_idx}")
                break
        
    if fila_header_idx is None:
        # print("fila_header_idx is None")
        return None

    fila_header_end = None
    for i in range(fila_header_idx,len(df_raw)):
        if df_raw.isna().iloc[i+1,0] and df_raw.isna().iloc[i+2,0]:
            fila_header_end = i
            # print(f"Fila final de la tabla: {fila_header_end}")
            break
    
    if fila_header_end is None:
        print("fila_header_end is None")

    df_raw = df_raw.replace(np.nan, None)
    df_variables= df_raw.iloc[fila_header_idx:fila_header_end+1,0]
    # print(f"{df_variables=}")
    # print(f"{df_variables[0]}")
    
    variables_dict, caudal_idx  = normalize_variables_tabla(caso, df_variables)
    # print(f"{variables_dict=}")
    # print(f"{caudal_idx=}")
    # print(f"{df_raw}=")
    final_col = 0
    for i in range(1,len(df_raw.columns)+1):
        if df_raw.iloc[caudal_idx,i] != 0:
            # print(f"{df_raw.iloc[caudal_idx,i]=}")
            pass
        else:
            final_col = i
            # print(f"Caudal = {df_raw.iloc[caudal_idx,i]}, {final_col=}")
            break
    
    values_dict = {}
    # print(f"{variables_dict}")
    for var_dict in variables_dict:
        var, _ = var_dict.keys()
        # print(f"{var=}")
        idx = var_dict["idx"]
        # print(f"{var=} {idx=}")

        value_list = []
        for value in df_raw.iloc[idx,1:final_col+1].tolist():
            try:
                value_list.append(float(value))
            except(ValueError, TypeError):
                value_list.append(None)
        if all(val is None for val in value_list):
            continue
        # values_dict[var] = df_raw.iloc[idx,1:final_col+1].tolist()
        values_dict[var] = value_list
    
    data = pd.DataFrame(values_dict)
    return data
    # print(f"{data=}")


