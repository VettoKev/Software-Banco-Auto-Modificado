from db.db_manager import DatabaseManager
from db.repos import EnsayoRepository, BombaRepository, MedicionRepository
from db.models import Bomba
from db.field_map import (
    normalize_data_select,
    normalize_overrides,
    normalize_df_data,
    normalize_data_select_name,
)

from ingestion.parser_metadata import extrear_metadatos_excel
from ingestion.parser_tabla import extraer_datos_ensayo
from ingestion.template_map import _UNITS_MAP

import pandas as pd
import os
import sys

variables_dict = [
        {"label": "Pe", "unit": "mca", "slave": 4},
        {"label": "Ps", "unit": "mca", "slave": 6},
        {"label": "Ps-Pe", "unit": "mca", "slave": 8},
        {"label": "T_amb", "unit": "°C", "slave": 5},
        {"label": "T_H2O", "unit": "°C", "slave": 7},
        {"label": "Caudal", "unit": "L/h", "slave": 2},
        {"label": "V1", "unit": "V", "slave": "Janitza"},
        {"label": "V2", "unit": "V", "slave": "Janitza"},
        {"label": "V3", "unit": "V", "slave": "Janitza"},
        {"label": "I1", "unit": "A", "slave": "Janitza"},
        {"label": "I2", "unit": "A", "slave": "Janitza"},
        {"label": "I3", "unit": "A", "slave": "Janitza"},
        {"label": "Pot1", "unit": "W", "slave": "Janitza"},
        {"label": "Pot2", "unit": "W", "slave": "Janitza"},
        {"label": "Pot3", "unit": "W", "slave": "Janitza"},
        {"label": "Fact P1", "unit": "-", "slave": "Janitza"},
        {"label": "Fact P2", "unit": "-", "slave": "Janitza"},
        {"label": "Fact P3", "unit": "-", "slave": "Janitza"},
        {"label": "f1", "unit": "Hz", "slave": "Janitza"},
        {"label": "f2", "unit": "Hz", "slave": "Janitza"},
        {"label": "f3", "unit": "Hz", "slave": "Janitza"},
        {"label": "U_Cap", "unit": "V", "slave": 10},
        {"label": "U_BA", "unit": "V", "slave": 9},
]
variables = [v["label"] for v in variables_dict]

carpeta_excluir = ["1.-Importadas","Intelijet","Max 20-1","Max 270 E","Tempo 7-1 Sanitaria","Max 26 Trifasico","5-1",
                    "GM 24 220V AR (Tandem 24)","Max 28 VF","Multietapa (proyecto)","415 GT 8 (Tandem 410)","Max 35VF",
                    "Max 45VF"]
csvDirectory = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\datos_adquiridos"
basePath = "\\\\rowasr010\\Ingenieria\\LABORATORIO\\General Laboratorio\\Bombas"

csvFiles = os.listdir(csvDirectory)
csvFileNames = [os.path.splitext(f)[0] for f in csvFiles]

bombas = os.listdir(basePath)

db            = DatabaseManager()
ensayo_repo   = EnsayoRepository(db=db)
bomba_repo    = BombaRepository(db=db)
medicion_repo = MedicionRepository(db=db)

# ensayo_en_db = ensayo_repo.get_all()
# print(ensayo_repo.get_all())

n_ensayos_tot    = 0
n_ensayos_csv    = 0
n_ensayos_manual = 0

for bomba in os.listdir(basePath):
    print("="*30)
    print(bomba)

    if bomba in carpeta_excluir:
        print(f"Se saleta {bomba=}")
        continue
    
    bombaPath     = os.path.join(basePath,bomba)
    carpeta_excel = os.path.join(bombaPath,"Ensayos")
    if not os.path.isdir(carpeta_excel):
        carpeta_excel = os.path.join(bombaPath,"Curvas caracteristicas")
    if not os.path.isdir(carpeta_excel):
        print(f"No existe la carpeta {carpeta_excel}, se saltea {bomba}")
        continue

    current_bomba = bomba_repo.get_by_name(bomba)
    data_select   = bomba_repo.get_data_select(current_bomba)
    # data_select = normalize_data_select(data_select)
    # print(f"{current_bomba.__dict__=}")

    for ensayo in os.listdir(carpeta_excel):
        num_ensayo, extension = os.path.splitext(ensayo)

        # print(f"{ensayo=} => {num_ensayo=}, {extension=}")
        if extension != ".xlsx" or "~" in ensayo: 
            print(f"se saltea {ensayo=}, no es .xlsx")
            continue
        n_ensayos_tot += 1

        existing = ensayo_repo.get_by_num_ensayo(num_ensayo)
        if existing is not None:
            print(f"{num_ensayo} ya está cargado a la db")
            continue

        print(f"{num_ensayo} no está cargado a la db => se procede a cargar")

        ensayo_dir = os.path.join(carpeta_excel,ensayo)
        extracted_metadata = extrear_metadatos_excel(ensayo_dir)

        raw_overrides = {**extracted_metadata, "num_ensayo": num_ensayo}
        overrides = normalize_overrides(raw_overrides)

        if num_ensayo in csvFileNames:
            n_ensayos_csv += 1
            print(f"{num_ensayo} está guardado en csv, dir: {ensayo_dir=}")

            data_df = pd.read_csv(os.path.join(csvDirectory,num_ensayo+".csv"), sep=";")
            normalized_data = normalize_df_data(data_df)

            max_idx      = normalized_data["Caudal"].idxmax()
            max_caudal   = normalized_data["Caudal"].max()
            nearest_mult = round(max_caudal/500)*500

            normalized_data["Caudal"] = (normalized_data["Caudal"]/500).round() * 500

            if abs(max_caudal - nearest_mult) > 150:
                print(f"Se mantiene el {max_caudal=}")
                normalized_data.loc[max_idx, "Caudal"] = max_caudal

            normalized_data.drop(normalized_data.shape[0]-1, inplace=True)
            # print(f"{normalized_data=}")

            try:
                ensayo_id = ensayo_repo.create(current_bomba, overrides)
                for _, row in normalized_data.iterrows():
                    caudal = row.get("Caudal", 0.0)
                    mediciones = [
                        {"variable": normalize_data_select_name(var["label"]), "valor": row.get(var['label'], 0.0), "unit": var["unit"]}
                        for var in variables_dict
                        if var["label"] not in ("Caudal", "Horario") 
                        and normalize_data_select_name(var["label"]) is not None
                        and getattr(data_select, normalize_data_select_name(var["label"]), False)
                    ]
                    # print(f"{mediciones=}")
                    medicion_repo.save_punto(ensayo_id, caudal, mediciones)
                print(f"Guardado en DB: ensayo {num_ensayo}")
            except Exception as e:
                print(f"Error guardando en DB: {e}")

        else:
            n_ensayos_manual += 1
            print(f"{num_ensayo} no está en csv, parsing manual")

            caso = data_select.id
            df = extraer_datos_ensayo(path_excel=ensayo_dir, caso=caso)
            # print(f"{df=}")
            # row = df.iloc[0]
            # mediciones = [
            #             {"variable": var, "valor": float(row.get(var, 0.0)), "unit": _UNITS_MAP.get(var)}
            #             for var in df.columns
            #             if var not in ("Caudal", "Horario")
            #             and getattr(data_select, var, False)
            #         ]
            # print(f"{mediciones=}")
            # sys.exit(1)

            try:
                ensayo_id = ensayo_repo.create(current_bomba, overrides)
                for _, row in df.iterrows():
                    caudal = row.get("Caudal", 0.0)
                    mediciones = [
                        {"variable": var, "valor": row.get(var, 0.0), "unit": _UNITS_MAP.get(var)}
                        for var in df.columns
                        if var not in ("Caudal", "Horario")
                        and getattr(data_select, var, False)
                    ]
                    medicion_repo.save_punto(ensayo_id, caudal, mediciones)
                print(f"Guardado en DB: ensayo {num_ensayo}")
            except Exception as e:
                print(f"Error guardando en DB: {e}")

print("="*30)
print(f"Final Stats:\n{n_ensayos_tot=}\n{n_ensayos_csv=}\n{n_ensayos_manual=}")

