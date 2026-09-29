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

# Monofasico CON Variador 
def csv2xlsx_MonoVar(outputFile:str,title:str,df:pd.DataFrame,df_temporal:pd.DataFrame,datos_motor:dict,modeloBomba:str):
    print("Entra en csv2xlsx MonoVar")
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
    
    template_excel = os.path.join("GuardadoDatos","Templates","template_ensayo_monofasico_variador.xlsx") 
    template_word = os.path.join("GuardadoDatos","Templates","template_ensayo_monofasico_variador.docx")

    ubicacion_datos = {
        "V1": 6,
        "Caudal": 7,
        "Ps-Pe": 8,
        "rpm": 9,
        "I1": 20,
        "Pot1": 12,
    }

    wb = load_workbook(template_excel)
    ws_datos = wb["Datos"]
    ws = wb["Informe"]
    ws_chart = wb["Graficos"]
    ws_datos["I2"] = tension

    if datos_motor:
        ws_datos["B2"] = "M"+str(int(datos_motor["Motor"]))+"-P"+str(int(datos_motor["Paquete"]))
        ws_datos["A2"] = "Curva Caracteristica"
        ws_datos["C2"] = datos_motor["Bobinado"]
        ws_datos["H2"] = datos_motor["Variador"]
        ws_datos["I2"] = int(datos_motor["Variador frec"][:-2])
        ws["N4"] = int(datos_motor["Variador frec"][:-2])
        ws_datos["F2"] = datos_motor["Caracol"]
        ws["K5"] = datos_motor["BP Diam"]
        ws_datos["D2"] = datos_motor["Turbina"]
        ws_datos["E2"] = datos_motor["Diametro Turbina"]
        ws["N5"] = datos_motor["Diametro Turbina"]

        # Bobinado ppal:
        BP_str = datos_motor["BP PE"]
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
                    ws["B31"] = n_espiras
                case 6:
                    ws["C31"] = n_espiras
                case 8:
                    ws["D31"] = n_espiras
                case 10:
                    ws["E31"] = n_espiras
                case 12:
                    ws["F31"] = n_espiras

    col_start = 2
    for key, value in ubicacion_datos.items():
        if key in df.columns:
            valores = df[key].tolist()
            for i, val in enumerate(valores, start=col_start):
                ws.cell(row=value, column= i, value=val)

    ws['AD27'] = df_temporal["Horario"].iloc[0][0:5]    # Completa la Casilla de Horario de Finalizacion
    ws['AD28'] = df_temporal["Horario"].iloc[-1][0:5]   # Completa la Casilla de Horario de Finalizacion
    ws['U27'] = df_temporal["T_amb"].iloc[0]
    ws['U28'] = df_temporal["T_amb"].iloc[-1]
    ws['X27'] = df_temporal["T_H2O"].iloc[0]
    ws['X28'] = df_temporal["T_H2O"].iloc[-1]

    # Cracion de graficos en la hoja "Graficos"
    # PvsQ
    x_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=7,max_row=7)
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=8,max_row=8)

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
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=18,max_row=18)

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
        "I1": 5,
        "Pot1": 6, 
        "rpm": 7
    }

    talba_datos_2 = doc.tables[2]
    for key, value in ubicacion_datos_word.items():
        if key in df.columns:
            valores = df[key].tolist()
            for i, val in enumerate(valores, start= 1):
                font_editor(talba_datos_2,fila= i,columna = value, dato = val)

    tabla_IvsF = doc.tables[1]
    font_editor(tabla_IvsF,fila = 5, columna = 4, dato =str(df_temporal["T_amb"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 5, columna = 5, dato =str(df_temporal["T_amb"].iloc[-1]), negrita = True)
    font_editor(tabla_IvsF,fila = 6, columna = 4, dato =str(df_temporal["T_H2O"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 6, columna = 5, dato =str(df_temporal["T_H2O"].iloc[-1]), negrita = True)
    font_editor(tabla_IvsF,fila = 7, columna = 4, dato =str(df_temporal["Horario"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 7, columna = 5, dato =str(df_temporal["Horario"].iloc[-1]), negrita = True)

    if datos_motor:
        tabla_ppal = doc.tables[0]
        font_editor(tabla_ppal,fila = 0, columna = 0, dato = "BOMBA: "+ modeloBomba,font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila = 1, columna = 0, dato= "MOTOR: M"+ str(int(datos_motor["Motor"]))+"-P"+str(int(datos_motor["Paquete"])),
                    negrita=True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila = 2, columna = 0, dato = "CARACOL: "+datos_motor["Caracol"], font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila=2,columna=2,dato="TURBINA: "+str(datos_motor["Turbina"])+" Ø"+str(datos_motor["Diametro Turbina"])+" mm",
                    negrita=True,centrado_vertical=False,centrado_horizontal=False)
        font_editor(tabla_ppal,fila = 3, columna=0, dato= "VARIADOR: "+datos_motor["Variador"]+" ("+str(int(tension))+"-"+str(int(frec))+"Hz)", 
                    negrita= True,centrado_horizontal=False, centrado_vertical= False)
        for p in doc.paragraphs:
            if p.text.strip().startswith("Datos del Bobinado:"):
                for run in p.runs:
                    run.text = ""

                add_run_header(p,"Datos del Bobinado:", font_size=14)
                add_run_header(p," BP " + str(datos_motor["BP PE"]) + " " + str(datos_motor["BP Diam"]) + " mm      ",
                                negrita=False,subrallado= False, font_size=14)
                add_run_header(p,"Ps-Pe (Qv=0, en frio)", font_size=14)
                add_run_header(p,"        ",subrallado=False, font_size=14)
                add_run_header(p,"Frecuencia:", font_size=14)
                add_run_header(p," "+datos_motor["Variador frec"], negrita= False, subrallado= False, font_size=14)
                break
    
    output_file_word = outputFile[:-5] + ".docx"
    print(f"Guardado en formato word como {output_file_word} COMPLETAR Y BORRAR")
    doc.save(output_file_word)
    wb.save(outputFile)
    print("Guardado Correctamente como: ", outputFile)
