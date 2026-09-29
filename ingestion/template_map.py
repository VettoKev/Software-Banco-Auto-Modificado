import pandas as pd

_MONOFASICO_MAP = {
    "U línea (V)"  : "V1",
    "U linea (V)"  : "V1",
    "Caudal"       : "Caudal",
    "Ps-Pe"        : "Ps_Pe",
    "rpm"          : "rpm",
    "It"           : "I1",
    "Ip"           : "I2",
    "Ia"           : "I3",
    "Pot. Total"   : "Pot1",
    "Pot Total [W]": "Pot1",
    "Pot. BP"      : "Pot2",
    "Pot. BA"      : "Pot3",
    "U capacitor"  : "U_Cap",
    "Tensión Ba"   : "U_BA",
    "Tension Ba"   : "U_BA"
}

_MONOFASICO_VARIADOR_MAP = {
    "Tensión"       : "V1",
    "Caudal"        : "Caudal",
    "Ps-Pe"         : "Ps_Pe",
    "rpm"           : "rpm",
    "I var. Janitza": "I1",
    "Pot. Var."     : "Pot1"
}

_TRIFASICO_MAP = {
    "Caudal"            : "Caudal",
    "Ps-Pe"             : "Ps_Pe",
    "rpm"               : "rpm",
    "Pot. Var. (Fase R)": "Pot1",
    "Pot. Var. (Fase S)": "Pot2",
    "Pot. Var. (Fase T)": "Pot3",
    "I Var. (Fase R)"   : "I1",
    "I Var. (Fase S)"   : "I2",
    "I Var. (Fase T)"   : "I3",
}

map_dict = {
    1: _MONOFASICO_MAP,
    2: _TRIFASICO_MAP,
    3: _MONOFASICO_VARIADOR_MAP
}

_UNITS_MAP = {
    "Caudal": "L/h",
    "Pe"    : "mca",
    "Ps"    : "mca",
    "Ps_Pe" : "mca",
    "rpm"   : "-",
    "I1"    : "A",
    "I2"    : "A",
    "I3"    : "A",
    "Pot1"  : "W",
    "Pot2"  : "W",
    "Pot3"  : "W",
    "V1"    : "V",
    "V2"    : "V",
    "V3"    : "V",
    "U_Cap" : "V",
    "U_BA"  : "V",
    "FactP1": "-",
    "FactP2": "-",
    "FactP3": "-",
}

def normalize_variables_tabla(caso: int, raw: pd.DataFrame) -> tuple[list[dict] | None, int]:
    template_map = map_dict[caso]
    # print(f"{template_map=}")
    caudal_idx = None
    result = []
    for idx,var in raw.items():
        if var:
            if var.rstrip() in template_map:
                result.append({
                    template_map[var.rstrip()]: var,
                    "idx"                     : idx,
                }) 
                if template_map[var.rstrip()] == "Caudal":
                    caudal_idx = idx
            else:
                # print(f"[normalize table] Variable not detected {var=} dropped")
                pass
    return result, caudal_idx
