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

# Trifasico
def csv2xlsx_Trifasico(outputFile:str,title:str,df:pd.DataFrame,df_temporal:pd.DataFrame,datosMotor:dict):
    print("Entra en csv2xlsx Trifasico")
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
    
    frec = round(df["f1"].iloc[0],-1)
    n_tensiones = [220, 127, 380]
    tension_ensayo = df["V1"].iloc[0]
    tension = min(n_tensiones,key=lambda x: abs(x-tension_ensayo))
    dimensions = df.shape
    last_row = dimensions[0]-1
    
    template_excel = os.path.join("GuardadoDatos","Templates","template_ensayo_trifasico.xlsx") 
    template_word = os.path.join("GuardadoDatos","Templates","template_ensayo_trifasico.docx")

    ubicacion_datos = {
        "Caudal": 6,
        "Ps-Pe": 7,
        "rpm": 8,
        "I1": 22,
        "I2": 23,
        "I3": 24,
        "Pot1": 18,
        "Pot2": 19,
        "Pot3": 20,
    }

    wb = load_workbook(template_excel)
    ws_datos = wb["Datos"]
    ws = wb["Informe"]
    ws_chart = wb["Graficos"]

    ws_datos["B2"] = tension
    ws_datos["F2"] = frec

    if datosMotor:
        ws_datos["A2"] = datosMotor["Motor"]
        ws_datos["C2"] = datosMotor["Paquete"]
        ws_datos["D2"] = datosMotor["Bobinado"]
        ws["N4"] = frec
        ws_datos["I2"] = datosMotor["Caracol"]
        ws["K5"] = datosMotor["BP Diam"]
        ws_datos["G2"] = datosMotor["Turbina"]
        ws_datos["H2"] = datosMotor["Diametro Turbina"]
        ws["N5"] = datosMotor["Diametro Turbina"]

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
                    ws["B46"] = n_espiras
                case 6:
                    ws["C46"] = n_espiras
                case 8:
                    ws["D46"] = n_espiras
                case 10:
                    ws["E46"] = n_espiras
                case 12:
                    ws["F46"] = n_espiras
    
    col_start = 2
    for key, value in ubicacion_datos.items():
        if key in df.columns:
            valores = df[key].tolist()
            for i, val in enumerate(valores, start=col_start):
                ws.cell(row=value, column= i, value=val)
    
    ws['AD42'] = df_temporal["Horario"].iloc[0][0:5]    # Completa la Casilla de Horario de Finalizacion
    ws['AD43'] = df_temporal["Horario"].iloc[-1][0:5]   # Completa la Casilla de Horario de Finalizacion
    ws['U42'] = df_temporal["T_amb"].iloc[0]
    ws['U43'] = df_temporal["T_amb"].iloc[-1]
    ws['X42'] = df_temporal["T_H2O"].iloc[0]
    ws['X43'] = df_temporal["T_H2O"].iloc[-1]

    # Cracion de graficos en la hoja "Graficos"
    # PvsQ
    x_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=6,max_row=6)
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=7,max_row=7)

    chart1 = ScatterChart(scatterStyle="lineMarker")
    chart1.title = "Delta_P vs Q"
    chart1.x_axis.title = "Caudal [L/h]"
    chart1.y_axis.title = "Delta_P [mca]"
    series = Series(y_values,x_values)
    series.marker = Marker("diamond", size=8)
    data_labels = DataLabelList()
    data_labels.showVal = True
    series.dLbls = data_labels
    chart1.series.append(series)

    chart1.width = 30
    chart1.height = 12.5
    ws_chart.add_chart(chart1, "B2")

    # Rendimiento Bomba:
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=16,max_row=16)

    chart_rendimiento = ScatterChart(scatterStyle="lineMarker")
    chart_rendimiento.title = "Rendimiento Bomba"
    chart_rendimiento.x_axis.title = "Caudal [L/h]"
    chart_rendimiento.y_axis.title = "Eta [%]"
    series = Series(y_values,x_values)
    series.marker = Marker("diamond",size=8)
    series.dLbls = data_labels
    chart_rendimiento.series.append(series)

    chart_rendimiento.width = 30
    chart_rendimiento.height = 12.5
    ws_chart.add_chart(chart_rendimiento,"B31")

    output_file_word = outputFile[:-5] + ".docx"
    print(f"Guardado en formato word como {output_file_word} COMPLETAR Y BORRAR")
    # doc.save(output_file_word)
    wb.save(outputFile)
    print("Guardado Correctamente como: ", outputFile)

