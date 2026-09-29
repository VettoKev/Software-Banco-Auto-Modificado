from openpyxl import load_workbook
from openpyxl.chart import ScatterChart, Series, Reference
from openpyxl.chart.marker import Marker
from openpyxl.chart.label import DataLabelList
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
import os
import pandas as pd

# Ensayo de Vacio
def csv2xlsx_Vacio(outputFile:str,title:str,df:pd.DataFrame,df_temporal:pd.DataFrame,datosMotor:dict,modeloBomba:str):
    print("Entra en csv2xlsx Vacio")
    def font_editor(tabla, fila, columna, dato, font_size = 14, negrita = False, centrado_vertical = True, centrado_horizontal = True):
            cell = tabla.cell(fila,columna)

            p = cell.paragraphs[0]
            p.text = ""
            run = p.add_run(str(dato))

            run.bold = negrita
            run.font.size = Pt(font_size)

            if centrado_vertical:
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            
            if centrado_horizontal:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def add_run_header(p, texto, negrita = True, subrallado = True, font_size = 18):
            run = p.add_run(texto)
            run.bold = negrita
            run.underline = subrallado
            run.font.size = Pt(font_size)
    
    df_tension = df.sort_values(by="V1")
    
    template_excel = os.path.join("GuardadoDatos","Templates","template_ensayo_monofasico.xlsx") 
    template_word = os.path.join("GuardadoDatos","Templates","template_ensayo_vacio.docx")

    ubicacion_datos = {
        "V1": 6,
        "rpm": 9,
        "I1": 10,
        "I2": 11,
        "I3": 13,
        "Pot1": 16,
        "Pot2": 36,
        "Pot3": 37,
        "U_Cap": 26,
        "U_BA": 30
    }

    wb = load_workbook(template_excel)
    ws_datos = wb["Datos"]
    ws = wb["Informe"]
    ws_chart = wb["Graficos"]

    if datosMotor:
            ws_datos["A2"] = datosMotor["Motor"]
            ws_datos["D2"] = datosMotor["Paquete"]
            ws_datos["F2"] = datosMotor["Capa Nominal"]
            ws["N4"] = datosMotor["Capa Nominal"]
            ws_datos["J2"] = datosMotor["Caracol"]
            ws["K4"] = datosMotor["BP Diam"]
            ws["K5"] = datosMotor["BA Diam"]
            
            # Bobinado ppal:
            BP_str = datosMotor["BP PE"]
            barra = BP_str.find("/")
            pasos = []
            pasos_aux = 0
            pasos_str = BP_str[0:barra]
            for index, char in enumerate(pasos_str):
                if char == "-":
                    pasos.append(int(pasos_str[pasos_aux:index]))
                    pasos_aux = index + 1
            pasos.append(int(pasos_str[pasos_aux:]))

            espiras = []
            espiras_str = BP_str[barra+1:]
            espiras_aux = 0
            for index, char in enumerate(espiras_str):
                if char == "-":
                    espiras.append(int(espiras_str[espiras_aux:index]))
                    espiras_aux = index + 1
            espiras.append(int(espiras_str[espiras_aux:]))

            for i, item in enumerate(pasos):
                n_espiras = espiras[i]
                match item:
                    case 4:
                        ws["B48"] = n_espiras
                    case 6:
                        ws["C48"] = n_espiras
                    case 8:
                        ws["D48"] = n_espiras
                    case 10:
                        ws["E48"] = n_espiras
                    case 12:
                        ws["F48"] = n_espiras
            
            # Bobinado Aux:
            BA_str = datosMotor["BA PE"]
            barra = BA_str.find("/")
            pasos = []
            pasos_aux = 0
            pasos_str = BA_str[0:barra]
            for index, char in enumerate(pasos_str):
                if char == "-":
                    pasos.append(int(pasos_str[pasos_aux:index]))
                    pasos_aux = index + 1
            pasos.append(int(pasos_str[pasos_aux:]))

            espiras = []
            espiras_str = BA_str[barra+1:]
            espiras_aux = 0
            for index, char in enumerate(espiras_str):
                if char == "-":
                    espiras.append(int(espiras_str[espiras_aux:index]))
                    espiras_aux = index + 1
            espiras.append(int(espiras_str[espiras_aux:]))

            for i, item in enumerate(pasos):
                n_espiras = espiras[i]
                match item:
                    case 6:
                        ws["I48"] = n_espiras
                    case 8:
                        ws["J48"] = n_espiras
                    case 10:
                        ws["K48"] = n_espiras
                    case 12:
                        ws["L48"] = n_espiras

    # Carga de datos a la hoja "Informe"
    col_start = 2
    for key, value in ubicacion_datos.items():
        if key in df_tension.columns:
            valores = df_tension[key].tolist()
            for i, val in enumerate(valores, start=col_start):
                ws.cell(row=value, column= i, value=val)
    
    ws['AD44'] = df_temporal["Horario"].iloc[0][0:5]    # Completa la Casilla de Horario de Finalizacion
    ws['AD45'] = df_temporal["Horario"].iloc[-1][0:5]   # Completa la Casilla de Horario de Finalizacion
    ws['U44'] = df_temporal["T_amb"].iloc[0]
    ws['U45'] = df_temporal["T_amb"].iloc[-1]
    ws['X44'] = df_temporal["T_H2O"].iloc[0]
    ws['X45'] = df_temporal["T_H2O"].iloc[-1]

    doc = Document(template_word)
    section = doc.sections[0]
    header = section.header
    
    for p in header.paragraphs:
        for run in p.runs:
            p.run = ""
        
        add_run_header(p,"Ensayo de Características:")
        add_run_header(p," "*10, subrallado=False)
        add_run_header(p,"FECHA:")
        add_run_header(p," " + title[0:2]+"/"+title[2:4]+"/"+title[4:6]+ " "*8, subrallado=False)
        add_run_header(p,"N° de Ensayo:")
        add_run_header(p," "+title+" "*6, subrallado= False)
        add_run_header(p,"Hoja N°:")
        add_run_header(p," "*2 + "de" + " "*3,subrallado= False)

    ubicacion_datos_word ={
        "V1": 0,
        "Pot1": 1,
        "Pot2": 2,
        "Pot3": 3,
        "I1": 4,
        "I2": 5,
        "I3": 6,
        "U_BA":7,
        "U_Cap":8,
        "rpm": 9
    }

    talba_datos_2 = doc.tables[2]
    for key, value in ubicacion_datos_word.items():
        if key in df_tension.columns:
            valores = df_tension[key].tolist()
            for i, val in enumerate(valores, start= 1):
                font_editor(talba_datos_2,fila= i,columna = value, dato = val)

    tabla_IvsF = doc.tables[1]
    font_editor(tabla_IvsF,fila = 5, columna = 2, dato =str(df_temporal["T_amb"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 5, columna = 3, dato =str(df_temporal["T_amb"].iloc[-1]), negrita = True)
    font_editor(tabla_IvsF,fila = 6, columna = 2, dato =str(df_temporal["T_H2O"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 6, columna = 3, dato =str(df_temporal["T_H2O"].iloc[-1]), negrita = True)
    font_editor(tabla_IvsF,fila = 7, columna = 2, dato =str(df_temporal["Horario"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 7, columna = 3, dato =str(df_temporal["Horario"].iloc[-1]), negrita = True)

    if datosMotor:
        tabla_ppal = doc.tables[0]
        font_editor(tabla_ppal,fila = 0, columna = 0, dato = "BOMBA: "+modeloBomba,font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila = 1, columna = 0, dato= "MOTOR: M"+ str(int(datosMotor["Motor"]))+"-P"+str(int(datosMotor["Paquete"])),
                    negrita=True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila = 2, columna = 0, dato = "CARACOL: "+datosMotor["Caracol"], font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        for p in doc.paragraphs:
            if p.text.strip().startswith("Datos del Bobinado:"):
                for run in p.runs:
                    run.text = ""

                add_run_header(p,"Datos del Bobinado:", font_size=14)
                add_run_header(p," BP " + str(datosMotor["BP PE"]) + " " + str(datosMotor["BP Diam"]) + " mm      "
                                + "BA " + str(datosMotor["BA PE"]) + " " + str(datosMotor["BA Diam"]) + " mm",subrallado= False, font_size=14)
                break
            
    output_file_word = outputFile[:-5] + ".docx"
    print(f"Guardado en formato word como {output_file_word} COMPLETAR Y BORRAR")
    doc.save(output_file_word)
    wb.save(outputFile)
    print("Guardado Correctamente como: ", outputFile)

