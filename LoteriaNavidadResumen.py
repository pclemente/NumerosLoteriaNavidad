import json
from datetime import datetime
import os

jsonFileName = "LoteriaNavidadResumen.json"
jsonFileNameLoad = "LoteriaNavidad.json"

# Define variables
timestamp_now = int(datetime.now().timestamp())
status = 4
numero1 = 88008
numero2 = 58303
numero3 = 31938
numero4 = 93361
numero5 = 41147
numero6 = 54274
numero7 = 45353
numero8 = 88979
numero9 = 92023
numero10 = 1568
numero11 = 86007
numero12 = 57421
numero13 = 37038
fraseSorteoPDF = ''
fraseListaPDF = ''
listaPDF = ''
urlAudio = ''
error = 0

# Create dictionary
premios = {
    'timestamp': timestamp_now,
    'status': status,
    'numero1': numero1,
    'numero2': numero2,
    'numero3': numero3,
    'numero4': numero4,
    'numero5': numero5,
    'numero6': numero6,
    'numero7': numero7,
    'numero8': numero8,
    'numero9': numero9,
    'numero10': numero10,
    'numero11': numero11,
    'numero12': numero12,
    'numero13': numero13,
    'fraseSorteoPDF': fraseSorteoPDF,
    'fraseListaPDF': fraseListaPDF,
    'listaPDF': listaPDF,
    'urlAudio': urlAudio,
    'error': error
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

    '''
    json_load_file = os.path.join(script_dir, jsonFileNameLoad)
    with open(json_load_file, 'r') as json_file:
        data_dict = json.load(json_file)

    # Look for a value of 4000000
    target_value = 4000000
    values_to_check = [target_value, target_value + 200, target_value + 1000, target_value + 1200]
    found = False

    for key, value in data_dict.items():
        if int(value) == target_value:
            found = True
            print(f"Key {key} has the desired value of {target_value}.")

    if not found:
        print(f"No key with the value of {target_value} found.")

    '''