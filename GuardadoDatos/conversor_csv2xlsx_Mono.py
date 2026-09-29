from openpyxl import load_workbook
from openpyxl.chart import ScatterChart, Series, Reference
from openpyxl.chart.marker import Marker
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.error_bar import ErrorBars
from openpyxl.chart.data_source import NumDataSource, NumData, NumVal, NumRef
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL
import os
import pandas as pd

# Monofasico y NO tiene Variador
def csv2xlsx_Mono(outputFile:str,title:str,df:pd.DataFrame,df_temporal:pd.DataFrame,datosMotor:dict,modeloBomba:str):
    print("Entra en csv2xlsx Mono")
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
    
    template_excel = os.path.join("GuardadoDatos","Templates","template_ensayo_monofasico.xlsx") 
    template_word = os.path.join("GuardadoDatos","Templates","template_ensayo_monofasico.docx")


    ubicacion_datos = {
        "V1": 6,
        "Caudal": 7,
        "Ps-Pe": 8,
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

    ws_datos["C2"] = frec
    ws_datos["B2"] = tension

    if datosMotor:
        ws_datos["A2"] = datosMotor["Motor"]
        ws_datos["D2"] = datosMotor["Paquete"]
        ws_datos["F2"] = datosMotor["Capa Nominal"]
        ws["N4"] = datosMotor["Capa Nominal"]
        ws_datos["J2"] = datosMotor["Caracol"]
        ws["K4"] = datosMotor["BP Diam"]
        ws["K5"] = datosMotor["BA Diam"]
        ws_datos["H2"] = datosMotor["Turbina"]
        ws_datos["I2"] = datosMotor["Diametro Turbina"]
        ws["N5"] = datosMotor["Diametro Turbina"]
        ws_datos["E2"] = datosMotor["Bobinado"]
        if "Control" in datosMotor:
            ws_datos["G2"] = datosMotor["Control"]
        
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
        if key in df.columns:
            valores = df[key].tolist()
            for i, val in enumerate(valores, start=col_start):
                ws.cell(row=value, column= i, value=val)
    
    ws['AD44'] = df_temporal["Horario"].iloc[0][0:5]    # Completa la Casilla de Horario de Finalizacion
    ws['AD45'] = df_temporal["Horario"].iloc[-1][0:5]   # Completa la Casilla de Horario de Finalizacion
    ws['U44'] = df_temporal["T_amb"].iloc[0]
    ws['U45'] = df_temporal["T_amb"].iloc[-1]
    ws['X44'] = df_temporal["T_H2O"].iloc[0]
    ws['X45'] = df_temporal["T_H2O"].iloc[-1]

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

    # Densidad de Corriente
    y_values_BP = Reference(ws, min_col=2, max_col=2+last_row, min_row=12,max_row=12)
    y_values_BA = Reference(ws, min_col=2, max_col=2+last_row, min_row=14,max_row=14)

    chart_Densidad = ScatterChart(scatterStyle="lineMarker")
    chart_Densidad.title = "Densidad de Corriente"
    chart1.x_axis.title = "Caudal [L/h]"
    chart1.y_axis.title = "Densidad [A/mm^2]"
    series_BP = Series(y_values_BP,x_values,title="Primario")
    series_BP.marker = Marker("diamond", size=8)
    series_BP.dLbls = data_labels
    series_BA = Series(y_values_BA,x_values,title="Auxiliar")
    series_BA.marker = Marker("diamond",size=8)
    series_BA.dLbls = data_labels
    chart_Densidad.series.append(series_BP)
    chart_Densidad.series.append(series_BA)

    chart_Densidad.width = 30
    chart_Densidad.height = 12.5
    ws_chart.add_chart(chart_Densidad, "B31")

    # Rendimiento Bomba:
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=19,max_row=19)

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
    ws_chart.add_chart(chart_rendimiento,"B62")
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
        "Pot2": 5,
        "Pot3": 6,
        "I1": 7,
        "I2": 8,
        "I3": 9,
        "U_BA":10,
        "U_Cap":11,
        "rpm": 12
    }

    talba_datos_2 = doc.tables[2]
    for key, value in ubicacion_datos_word.items():
        if key in df.columns:
            valores = df[key].tolist()
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
        font_editor(tabla_ppal,fila = 0, columna = 0, dato = "BOMBA: "+ modeloBomba, font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila = 1, columna = 0, dato= "MOTOR: M"+ str(int(datosMotor["Motor"]))+"-P"+str(int(datosMotor["Paquete"])),
                    negrita=True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila = 2, columna = 0, dato = "CARACOL: "+datosMotor["Caracol"], font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila=2,columna=2,dato="TURBINA: "+str(datosMotor["Turbina"])+" Ø"+str(datosMotor["Diametro Turbina"])+" mm",
                    negrita=True,centrado_vertical=False,centrado_horizontal=False)
        font_editor(tabla_ppal,fila = 3, columna = 0, dato = "CAPACITOR: "+str(datosMotor["Capa Nominal"]), font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
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

def df_auto2xlsx_mono(outputFile:str,title:str,dfMean:pd.DataFrame,dfStd:pd.DataFrame,metadata:dict,modeloBomba:str):
    print("Entra en csv2xlsx Mono")
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

    frec = round(dfMean["f1"].iloc[0],-1)
    n_tensiones = [220, 127, 380]
    tension_ensayo = dfMean["V1"].iloc[0]
    tension = min(n_tensiones,key=lambda x: abs(x-tension_ensayo))
    dimensions = dfMean.shape
    last_row = dimensions[0]-1
    df_temporal = dfMean.sort_values(by="Horario")
    
    template_excel = os.path.join("GuardadoDatos","Templates","template_ensayo_monofasico.xlsx") 
    template_word = os.path.join("GuardadoDatos","Templates","template_ensayo_monofasico.docx")

    ubicacion_datos = {
        "V1": 6,
        "Caudal": 7,
        "Ps-Pe": 8,
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
    ws_raw = wb.create_sheet("Raw Data")

    ws_datos["C2"] = frec
    ws_datos["B2"] = tension

    if metadata:
        ws_datos["A2"] = metadata["Motor"]
        ws_datos["D2"] = metadata["Paquete"]
        ws_datos["F2"] = metadata["Capa Nominal"]
        ws["N4"] = metadata["Capa Nominal"]
        ws_datos["J2"] = metadata["Caracol"]
        ws["K4"] = metadata["BP Diam"]
        ws["K5"] = metadata["BA Diam"]
        ws_datos["H2"] = metadata["Turbina"]
        ws_datos["I2"] = metadata["Diametro Turbina"]
        ws["N5"] = metadata["Diametro Turbina"]
        ws["E2"] = metadata["Bobinado"]
        
        # Bobinado ppal:
        BP_str = metadata["BP PE"]
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
        BA_str = metadata["BA PE"]
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
    i_var = 1
    for key, value in ubicacion_datos.items():
        if key in dfMean.columns:
            valores = dfMean[key].tolist()
            for i, val in enumerate(valores, start=col_start):
                ws.cell(row=value, column= i, value=val)
        # vuelca datos del promedio
        nombreVar = ws.cell(row=value, column= 1).value
        ws_raw.cell(row=1,column=(2*i_var)-1,value=nombreVar+" prom")
        valoresMean = dfMean[key].tolist()
        for i ,val in enumerate(valoresMean,start=2):
            ws_raw.cell(row=i,column=(2*i_var)-1,value=val)

        # lo mismo pero para la desviacion muestral
        ws_raw.cell(row=1,column=2*i_var,value=nombreVar+" std")
        valoresStd = dfStd[key].tolist()
        for i, val in enumerate(valoresStd,start=2):
            ws_raw.cell(row=i,column=(2*i_var),value=val)
        i_var += 1
    
    ws['AD44'] = df_temporal["Horario"].iloc[0][0:5]    # Completa la Casilla de Horario de Finalizacion
    ws['AD45'] = df_temporal["Horario"].iloc[-1][0:5]   # Completa la Casilla de Horario de Finalizacion
    ws['U44'] = df_temporal["T_amb"].iloc[0]
    ws['U45'] = df_temporal["T_amb"].iloc[-1]
    ws['X44'] = df_temporal["T_H2O"].iloc[0]
    ws['X45'] = df_temporal["T_H2O"].iloc[-1]

    # Cracion de graficos en la hoja "Graficos"
    # PvsQ
    x_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=7,max_row=7)
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=8,max_row=8)
    y_error_values = Reference(ws_raw,min_col=15,max_col=15,min_row=2,max_row=2+last_row)
    error_data = NumDataSource(NumRef(y_error_values))
    error_bars = ErrorBars(
        plus=error_data,
        minus=error_data,
        errDir= "y",
        errValType="cust"
    )

    chart1 = ScatterChart(scatterStyle="lineMarker")
    chart1.title = "Delta_P vs Q"
    chart1.x_axis.title = "Caudal [L/h]"
    chart1.y_axis.title = "Delta_P [mca]"
    series = Series(y_values,x_values)
    series.marker = Marker("diamond", size=8)
    data_labels = DataLabelList()
    data_labels.showVal = True
    series.dLbls = data_labels
    series.errBars = error_bars
    chart1.series.append(series)

    chart1.width = 30
    chart1.height = 12.5
    ws_chart.add_chart(chart1, "B2")

    # Densidad de Corriente
    y_values_BP = Reference(ws, min_col=2, max_col=2+last_row, min_row=12,max_row=12)
    y_values_BA = Reference(ws, min_col=2, max_col=2+last_row, min_row=14,max_row=14)

    chart_Densidad = ScatterChart(scatterStyle="lineMarker")
    chart_Densidad.title = "Densidad de Corriente"
    chart1.x_axis.title = "Caudal [L/h]"
    chart1.y_axis.title = "Densidad [A/mm^2]"
    series_BP = Series(y_values_BP,x_values,title="Primario")
    series_BP.marker = Marker("diamond", size=8)
    series_BP.dLbls = data_labels
    series_BA = Series(y_values_BA,x_values,title="Auxiliar")
    series_BA.marker = Marker("diamond",size=8)
    series_BA.dLbls = data_labels
    chart_Densidad.series.append(series_BP)
    chart_Densidad.series.append(series_BA)

    chart_Densidad.width = 30
    chart_Densidad.height = 12.5
    ws_chart.add_chart(chart_Densidad, "B31")

    # Rendimiento Bomba:
    y_values = Reference(ws, min_col=2, max_col=2+last_row, min_row=19,max_row=19)

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
    ws_chart.add_chart(chart_rendimiento,"B62")
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
        "Pot2": 5,
        "Pot3": 6,
        "I1": 7,
        "I2": 8,
        "I3": 9,
        "U_BA":10,
        "U_Cap":11,
        "rpm": 12
    }

    talba_datos_2 = doc.tables[2]
    for key, value in ubicacion_datos_word.items():
        if key in dfMean.columns:
            valores = dfMean[key].tolist()
            for i, val in enumerate(valores, start= 1):
                font_editor(talba_datos_2,fila= i,columna = value, dato = val)

    tabla_IvsF = doc.tables[1]
    font_editor(tabla_IvsF,fila = 5, columna = 2, dato =str(df_temporal["T_amb"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 5, columna = 3, dato =str(df_temporal["T_amb"].iloc[-1]), negrita = True)
    font_editor(tabla_IvsF,fila = 6, columna = 2, dato =str(df_temporal["T_H2O"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 6, columna = 3, dato =str(df_temporal["T_H2O"].iloc[-1]), negrita = True)
    font_editor(tabla_IvsF,fila = 7, columna = 2, dato =str(df_temporal["Horario"].iloc[0]), negrita = True)
    font_editor(tabla_IvsF,fila = 7, columna = 3, dato =str(df_temporal["Horario"].iloc[-1]), negrita = True)

    if metadata:
        tabla_ppal = doc.tables[0]
        font_editor(tabla_ppal,fila = 0, columna = 0, dato = "BOMBA: "+ modeloBomba, font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila = 1, columna = 0, dato= "MOTOR: M"+ str(int(metadata["Motor"]))+"-P"+str(int(metadata["Paquete"])),
                    negrita=True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila = 2, columna = 0, dato = "CARACOL: "+metadata["Caracol"], font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        font_editor(tabla_ppal,fila=2,columna=2,dato="TURBINA: "+str(metadata["Turbina"])+" Ø"+str(metadata["Diametro Turbina"])+" mm",
                    negrita=True,centrado_vertical=False,centrado_horizontal=False)
        font_editor(tabla_ppal,fila = 3, columna = 0, dato = "CAPACITOR: "+str(metadata["Capa Nominal"]), font_size = 14, negrita = True, centrado_vertical= False, centrado_horizontal= False)
        for p in doc.paragraphs:
            if p.text.strip().startswith("Datos del Bobinado:"):
                for run in p.runs:
                    run.text = ""

                add_run_header(p,"Datos del Bobinado:", font_size=14)
                add_run_header(p," BP " + str(metadata["BP PE"]) + " " + str(metadata["BP Diam"]) + " mm      "
                                + "BA " + str(metadata["BA PE"]) + " " + str(metadata["BA Diam"]) + " mm",subrallado= False, font_size=14)
                break
    output_file_word = outputFile[:-5] + ".docx"
    print(f"Guardado en formato word como {output_file_word} COMPLETAR Y BORRAR")
    doc.save(output_file_word)
    wb.save(outputFile)
    print("Guardado Correctamente como: ", outputFile)