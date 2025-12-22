import json
import os
from LoteriaNavidadStatusConstant import get_status, validate_status, get_status_description

jsonFileName = "LoteriaNavidadStatus.json"

# Get status from centralized constant file
status = get_status()
error_input = 0

print(f"Current lottery status: {status} - {get_status_description(status)}")

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

