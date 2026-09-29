import pandas as pd
import numpy as np
import sys
import re

def extrear_metadatos_excel(path_excel: str) -> dict:
    try:
        df = pd.read_excel(path_excel, sheet_name=0, header=None)
        # print(df)
        metadatos = buscar_metadatos_particulares(df)
        return metadatos
    except Exception as e:
        print(f"Error en archivo {path_excel}: {e}")

def buscar_metadatos_particulares(df:pd.DataFrame) -> dict:
    if df.shape[0] == 1:
        return None
    # Turbina
    metadata = {}
    diametroSeparado = False
    motorSeparado = False
    turbinaDiamList = ["Diametro","Ø"]
    turbinaList = ["TMA","Tango","30 Alabes","Bronce","30VF","30E","4-1","7-1","Calef"]
    caracolList = ["Tango","Max VSTD","Max VSTD 1.5\"","Max VAC 1\"","Max VAC 1.5\"",
                                    "4-1","7-1","12-1","15 1","15 1 Con Adaptador","Intelig"]
    controlList = ["NO","ECO","ECO Max","RPX","FLP","FL","Press"]

    headers = df.iloc[0].tolist()
    for header in headers:
        if any(cond in header for cond in turbinaDiamList):
            # print("Tiene Diam separado")
            diametroSeparado = True
    if "Paquete" in headers:
        motorSeparado = True
        # print("Motor separado")
    if "Control" not in headers:
        metadata["Control"] = "NO"
    for j in range(df.shape[1]):
        celda = str(df.iat[0,j])
        valor = df.iat[1,j]
        if celda == "Turbina":
            pos_turbina = j
            # print(celda)
            if "30 a" in valor.lower() or "30 á" in valor.lower():
                metadata["Turbina"] = "30 Alabes"
            elif "3D" in valor:
                metadata["Turbina"] = valor
                # print("Es 30 Alabes")
            elif any(cond.lower() in valor.lower() for cond in turbinaList):
                    if valor.lower() in ["tango","bronce"]:
                        metadata["Turbina"] = valor.capitalize()
                    elif "tango" in valor.lower():
                        metadata["Turbina"] = "Tango"
                    elif "30VF" in valor:
                        metadata["Turbina"] = "30VF"
                    elif "TMA" in valor:
                        metadata["Turbina"] = "TMA"
                    else:
                        metadata["Turbina"] = valor
                # print(f"Turbina: {valor}")
            elif "multialabes" in valor.lower():
                metadata["Turbina"] = "TMA"
                # print("TMA")
            elif all(digit.isdigit() for digit in valor):
                metadata["Turbina"] = valor
            else:
                sys.exit("No se encuentra turbina. Chequear ensayo")
            if not diametroSeparado :
                metadata["Turbina Diametro"] = extract_decimal_numbers(df.iat[1,pos_turbina])[0]
        if any(cond in celda for cond in turbinaDiamList) and diametroSeparado:
            # metadata["Turbina Diametro"] = extract_decimal_numbers(df.iat[1,j])[0]
            metadata["Turbina Diametro"] = extract_decimal_numbers(str(valor))[0]
        
        # Caracol
        if celda == "Caracol":
            if any(cond in valor for cond in caracolList):
                # print(valor)
                metadata["Caracol"] = valor
                if "15 1" in valor:
                    metadata["Caracol"] = valor.replace("15 1","15-1")
                elif "Tango" in valor:
                    metadata["Caracol"] = "Tango"
            elif "15" in valor and "1" in valor:
                metadata["Caracol"] = "15-1"
            elif "12" in valor:
                metadata["Caracol"] = "12-1"
            elif "Max 26" in valor or valor == "Max26 STD":
                metadata["Caracol"] = "Max VSTD"
            elif valor == "15-1":
                metadata["Caracol"] = valor
            elif (("1,5" in valor or "1.5" in valor) and "VAC" not in valor) or valor == "Max VAC":
                metadata["Caracol"] = "Max VSTD 1.5\""
            elif "VAC" in valor and "1\"" in valor:
                metadata["Caracol"] = "Max VAC 1\""
            elif "laton" in valor.lower() or "latón" in valor.lower():
                metadata["Caracol"] = "Max VSTD LATON"
            else:
                sys.exit("No se encuentra caracol. Chequear ensayo")
        
        if motorSeparado:
            if celda == "Motor":
                if isinstance(valor,str) and valor[0]=="M":
                    m,_ = valor.split('-')
                    metadata["Motor"] = int(m[1:])
                else:
                    metadata["Motor"] = int(valor)
            if celda == "Paquete":
                metadata["Paquete"] = int(valor)
        else:
            if celda == "Motor":
                m,p=valor.split('-')
                metadata["Motor"] = int(m[1:])
                metadata["Paquete"] = int(p[1:])

        # Control:
        if celda == "Control":
            if any(cond in valor for cond in controlList):
                metadata["Control"] = valor
            elif valor.lower() == "no" or "sin" in valor.lower() or "-" == valor:
                metadata["Control"] = "NO"
            elif "RPX" in valor:
                metadata["Control"] = "RPX"
            elif "ECO" in valor or "Electrónic" in valor or "eco" in valor.lower() or valor == "\"e\"":
                metadata["Control"] = "ECO"
            elif "FLP" in valor:
                metadata["Control"] = "FLP"
            elif valor.lower() == "press e":
                metadata["Control"] = "Press E"
            elif "press" in valor.lower():
                metadata["Control"] = "Press"
            else:
                sys.exit("No se econtro control. Chequear ensayo")

        # Capacitor:
        if "Capacitor" in celda:
            # metadata["Capacitor"] = extract_decimal_numbers(str(valor))
            if isinstance(valor,str):
                if valor[-2:].lower() == "uf":
                    metadata["Capacitor"] = float(valor[:-2])
                else:
                    metadata["Capacitor"] = float(valor)
            else:
                metadata["Capacitor"] = float(valor)

        # Bobinado:
        
        if celda == "Bobinado":
            if not isinstance(valor,str):
                metadata["Bobinado"] = "STD"
            elif "std" in valor.lower():
                metadata["Bobinado"] = "STD"
            else:
                metadata["Bobinado"] = valor
        
        if "variador" in celda.lower():
            metadata["Variador"] = valor

        if "frecuencia" in celda.lower():
            metadata["Frecuencia"] = extract_decimal_numbers(str(valor))[0]
        
        if "tension" in celda.lower():
            metadata["Tension"] = extract_decimal_numbers(str(valor))[0]

        if "comentario" in celda.lower():
            metadata["notas"] = str(valor) 
    # print(metadata)
    return metadata


def extract_decimal_numbers(text):
    """
    Extracts all floating point and integer numbers from a string.

    The regex pattern r'-?\d*\.?\d+' matches:
    - '-'? : an optional negative sign
    - \d*  : zero or more digits (for cases like '.556')
    - \,?  : an optional decimal point
    - \d+  : one or more digits after the point, or a whole number
    """
    # Find all matching number patterns as strings
    matches = re.findall(r'-?\d*\,?\d+', text)
    
    # Convert the matched strings to float or int as appropriate
    # if len(matches)>1:
    #     matches = matches[0]+'.'+matches[1]
    # print(matches)
    if any(',' in x for x in matches):
        for i,x in enumerate(matches):
            if ',' in x:
                matches[i]=x.replace(',','.') 
    return [float(x) if '.' in x else int(x) for x in matches]

