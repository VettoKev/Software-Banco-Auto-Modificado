PLC_COMMANDS = {
    "Habilitar Energia":{
        "sequence":[
            {"coils": {0:1, 3: 1, 4:0},"delay":0.5},
            {"coils": {2:1}, "delay":0}
        ]
    },
    "Cortar Energia":{
        "sequence":[
            {"coils": {0:0, 2:0 , 3:0 , 4:1 , 11: 1},"delay":0.5},
            {"coils": {11:0}, "delay":0}
        ]
    },
    "Arranque Monofasico":{
        "sequence":[
            {"coils": {3:0, 4:1, 5:1, 15:1},"delay":1},
            {"coils": {10:1}, "delay":0}
        ]
    },
    "Parar Monofasico":{
        "sequence":[
            {"coils": {4:0, 5:0, 10:0, 15:0, 3:1},"delay":0.5},
            {"coils": {11:1}, "delay":0.5},
            {"coils": {11:0}, "delay":0.5}
        ]
    },
    "Arranque Trifasico":{
        "sequence":[
            {"coils": {5:1}, "delay":1},
            {"coils": {10:1}, "delay":0}
        ]
    },
    "Parar Trifasico":{
        "sequence":[
            {"coils": {5:0, 10:0},"delay":0.5},
            {"coils": {11:1}, "delay":0.5},
            {"coils": {11:0}, "delay":0.5}
        ]
    },
}