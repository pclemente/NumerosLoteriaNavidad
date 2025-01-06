import json
from datetime import datetime
import os

jsonFileName = "LoteriaElNinoResumen.json"
jsonFileNameLoad = "LoteriaElNino.json"

# Define variables
timestamp_now = int(datetime.now().timestamp())
status = 4
primer_premio = 78908
segundo_premio = 6766
tercer_premio = 66777
extraccion_4cifras_1 = 0
extraccion_4cifras_2 = 0
extraccion_3cifras_1 = 0
extraccion_3cifras_2 = 0
extraccion_3cifras_3 = 0
extraccion_3cifras_4 = 0
extraccion_3cifras_5 = 0
extraccion_3cifras_6 = 0
extraccion_3cifras_7 = 0
extraccion_3cifras_8 = 0
extraccion_3cifras_9 = 0
extraccion_3cifras_10 = 0
extraccion_3cifras_11 = 0
extraccion_3cifras_12 = 0
extraccion_3cifras_13 = 0
extraccion_3cifras_14 = 0
extraccion_2cifras_1 = 0
extraccion_2cifras_2 = 0
extraccion_2cifras_3 = 0
extraccion_2cifras_4 = 0
extraccion_2cifras_5 = 0
reintegro_1 = 0
reintegro_2 = 0
reintegro_3 = 0

# Create dictionary
premios = {
    'timestamp': timestamp_now,
    'status': status,
    'Primer_premio': primer_premio,
    'Segundo_Premio': segundo_premio,
    'Tercer_Premio': tercer_premio,
    'Extraccion_4_cifras_1': extraccion_4cifras_1,
    'Extraccion_4_cifras_2': extraccion_4cifras_2,
    'Extraccion_3_cifras_1': extraccion_3cifras_1,
    'Extraccion_3_cifras_2': extraccion_3cifras_2,
    'Extraccion_3_cifras_3': extraccion_3cifras_3,
    'Extraccion_3_cifras_4': extraccion_3cifras_4,
    'Extraccion_3_cifras_5': extraccion_3cifras_5,
    'Extraccion_3_cifras_6': extraccion_3cifras_6,
    'Extraccion_3_cifras_7': extraccion_3cifras_7,
    'Extraccion_3_cifras_8': extraccion_3cifras_8,
    'Extraccion_3_cifras_9': extraccion_3cifras_9,
    'Extraccion_3_cifras_10': extraccion_3cifras_10,
    'Extraccion_3_cifras_11': extraccion_3cifras_11,
    'Extraccion_3_cifras_12': extraccion_3cifras_12,
    'Extraccion_3_cifras_13': extraccion_3cifras_13,
    'Extraccion_3_cifras_14': extraccion_3cifras_14,
    'Extraccion_2_cifras_1': extraccion_2cifras_1,
    'Extraccion_2_cifras_2': extraccion_2cifras_2,
    'Extraccion_2_cifras_3': extraccion_2cifras_3,
    'Extraccion_2_cifras_4': extraccion_2cifras_4,
    'Extraccion_2_cifras_5': extraccion_2cifras_5,
    'Reintegro_1': reintegro_1,
    'Reintegro_2': reintegro_2,
    'Reintegro_3': reintegro_3
}

def create_json_file(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)
        file.write('\n')

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = script_dir + "/output"

    print(script_dir)

    # Specify the file path
    output_file = os.path.join(script_dir, jsonFileName)

    print(output_file)

    # Provide the dictionary and file path
    create_json_file(premios, output_file)
