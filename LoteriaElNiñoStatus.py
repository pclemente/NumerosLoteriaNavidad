import json
import os

jsonFileName = "LoteriaElNinoStatus.json"

'''
0: El sorteo no ha comenzado aún. Todos los números aparecerán como no premiados.
1: El sorteo ha empezado. La lista de números premiados se va cargando poco a poco. Un número premiado podría llegar a tardar unos minutos en aparecer.
2: El sorteo ha terminado y la lista de números y premios debería ser la correcta aunque, tomada al oído, no podemos estar seguros de ella.
3: El sorteo ha terminado y existe una lista oficial en PDF.
4: El sorteo ha terminado y la lista de números y premios está basada en la oficial. De todas formas, recuerda que la única lista oficial es la que publica la ONLAE y deberías comprobar todos tus números contra ella.
'''


# Function to validate and set the status
def set_status(status_code):
    valid_statuses = {0, 1, 2, 3, 4}
    if status_code in valid_statuses:
        return status_code
    else:
        print("Invalid status code. Using default status (1).")
        return 1

# User input for status and error values
#status_input = int(input("Enter status code (0-4): "))
#error_input = int(input("Enter error code: "))
status_input = 0
error_input = 0

# Validate and set the status
status = set_status(status_input)

# Define the data
info = {
    'status': status,
    'error': error_input
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
    create_json_file(info, output_file)

