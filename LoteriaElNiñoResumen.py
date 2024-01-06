import json
from datetime import datetime
import os

jsonFileName = "LoteriaElNinoResumen.json"
jsonFileNameLoad = "LoteriaElNino.json"

# Define variables
timestamp_now = int(datetime.now().timestamp())
status = 4
primer_premio = 94974
segundo_premio = 89634
tercer_premio = 57033
extraccion_4cifras_1 = 7247
extraccion_4cifras_2 = 8172
extraccion_3cifras_1 = 507
extraccion_3cifras_2 = 296
extraccion_3cifras_3 = 161
extraccion_3cifras_4 = 978
extraccion_3cifras_5 = 872
extraccion_3cifras_6 = 506
extraccion_3cifras_7 = 114
extraccion_3cifras_8 = 488
extraccion_3cifras_9 = 730
extraccion_3cifras_10 = 428
extraccion_3cifras_11 = 281
extraccion_3cifras_12 = 568
extraccion_3cifras_13 = 644
extraccion_3cifras_14 = 598
extraccion_2cifras_1 = 66
extraccion_2cifras_2 = 40
extraccion_2cifras_3 = 32
extraccion_2cifras_4 = 65
extraccion_2cifras_5 = 99
reintegro_1 = 4
reintegro_2 = 1
reintegro_3 = 9

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
