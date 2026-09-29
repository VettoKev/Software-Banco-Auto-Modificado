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

def csv2xlsx_inverter(outputFile:str,title:str,df:pd.DataFrame,df_temporal:pd.DataFrame):
    print("Entra en csv2xlsx Inverter")
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
    
    template_excel = os.path.join("GuardadoDatos","Templates","template_ensayo_inverter.xlsx") 
    template_word = os.path.join("GuardadoDatos","Templates","template_ensayo_inverter.docx") 

    # que datos van en que fila. Nombre de encabezado de fila: Número de fila
    ubicacion_datos = {
        "V1": 2,
        "Caudal": 3,
        "Ps-Pe": 4,
        "rpm": 5,
        "I1": 6,
        "Pot1": 8,
    }

    wb = load_workbook(template_excel)
    ws_datos = wb["Datos"]
    ws = wb["Informe"]
    ws_chart = wb["Graficos"]

    ws_datos["B2"] = tension

    # Carga de datos a la hoja "Informe"
    col_start = 2
    for key, value in ubicacion_datos.items():
        if key in df.columns:
            valores = df[key].tolist()
            for i, val in enumerate(valores, start=col_start):
                ws.cell(row=value, column= i, value=val)
    
    ws['K18'] = df_temporal["Horario"].iloc[0][0:5]    # Completa la Casilla de Horario de Finalizacion
    ws['K19'] = df_temporal["Horario"].iloc[-1][0:5]   # Completa la Casilla de Horario de Finalizacion
    ws['B18'] = df_temporal["T_amb"].iloc[0]
    ws['B19'] = df_temporal["T_amb"].iloc[-1]
    ws['E18'] = df_temporal["T_H2O"].iloc[0]
    ws['E19'] = df_temporal["T_H2O"].iloc[-1]

    # Cracion de graficos en la hoja "Graficos"
    # PvsQ
    x_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=3,max_row=3)
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=4,max_row=4)

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
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=10,max_row=10)

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

    # ------------------------------------------------------------------- #
    # Guardado a Word

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
        "Caudal": 0,
        "Ps": 1,
        "Pe": 2,
        "Ps-Pe": 3,
        "Pot1": 4,
        "I1": 5,
        "rpm": 7
    }

    talba_datos_2 = doc.tables[1]
    for key, value in ubicacion_datos_word.items():
        if key in df.columns:
            valores = df[key].tolist()
            for i, val in enumerate(valores, start= 1):
                font_editor(talba_datos_2,fila= i,columna = value, dato = val)

    tabla_IvsF = doc.tables[0]
    font_editor(tabla_IvsF,fila = 2, columna = 4, dato =str(df_temporal["T_amb"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 2, columna = 10, dato =str(df_temporal["T_amb"].iloc[-1]), negrita = True)
    font_editor(tabla_IvsF,fila = 3, columna = 4, dato =str(df_temporal["T_H2O"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 3, columna = 10, dato =str(df_temporal["T_H2O"].iloc[-1]), negrita = True)
    font_editor(tabla_IvsF,fila = 4, columna = 4, dato =str(df_temporal["Horario"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 4, columna = 10, dato =str(df_temporal["Horario"].iloc[-1]), negrita = True)

    output_file_word = outputFile[:-5] + ".docx"
    print(f"Guardado en formato word como {output_file_word} COMPLETAR Y BORRAR")
    doc.save(output_file_word)
    wb.save(outputFile)
    print("Guardado Correctamente como: ", outputFile)

