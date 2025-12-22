import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import subprocess
from LoteriaNavidadStatusConstant import get_status

jsonFileName = "LoteriaNavidadResumen.json"

# URL to parse
url = "https://www.rtve.es/loterias/loteria-navidad/"

def create_json_file(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)
        file.write('\n')

def parse_rtve_loteria_resumen():
    """
    Parse RTVE lottery main page to extract the main prizes (Gordo, Segundo, Tercero, etc.)
    Returns a dictionary with the prizes or -1 if they haven't appeared yet
    """
    
    # Initialize default values (numbers not drawn yet)
    timestamp_now = int(datetime.now().timestamp())
    status = get_status()
    # Primer premio (El Gordo)
    numero1 = -1
    # Segundo premio
    numero2 = -1
    # Tercer premio
    numero3 = -1
    # Primer Cuarto
    numero4 = -1
    # Segundo Cuarto
    numero5 = -1
    # Primer Quinto
    numero6 = -1
    # Segundo Quinto
    numero7 = -1
    # Tercer Quinto
    numero8 = -1
    # Cuarto Quinto
    numero9 = -1
    # Quinto Quinto
    numero10 = -1
    # Sexto Quinto
    numero11 = -1
    # Septimo Quinto
    numero12 = -1
    # Octavo Quinto
    numero13 = -1
    fraseSorteoPDF = ''
    fraseListaPDF = ''
    listaPDF = ''
    urlAudio = ''
    error = 0
    
    try:
        # Disable SSL verification warnings (use with caution)
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        
        # Fetch the HTML content of the webpage
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main lottery results container
            # The prizes are in <ol id="viewLoteria2025">
            lottery_container = soup.find('ol', id='viewLoteria2025')
            
            if lottery_container:
                print("Found lottery container, extracting prizes...")
                
                # Extract El Gordo (1st prize) - class p1
                p1 = lottery_container.find('li', class_='p1')
                if p1:
                    span = p1.find('span')
                    if span and span.text.strip():
                        numero1 = span.text.strip()
                        print(f"El Gordo: {numero1}")
                
                # Extract Segundo (2nd prize) - class p2
                p2 = lottery_container.find('li', class_='p2')
                if p2:
                    span = p2.find('span')
                    if span and span.text.strip():
                        numero2 = span.text.strip()
                        print(f"Segundo: {numero2}")
                
                # Extract Tercero (3rd prize) - class p3
                p3 = lottery_container.find('li', class_='p3')
                if p3:
                    span = p3.find('span')
                    if span and span.text.strip():
                        numero3 = span.text.strip()
                        print(f"Tercero: {numero3}")
                
                # Extract Cuarto (4th prizes - 2 prizes) - class p4
                p4 = lottery_container.find('li', class_='p4')
                if p4:
                    cuartos = p4.find_all('span')
                    if len(cuartos) >= 1 and cuartos[0].text.strip():
                        numero4 = cuartos[0].text.strip()
                        print(f"Primer Cuarto: {numero4}")
                    if len(cuartos) >= 2 and cuartos[1].text.strip():
                        numero5 = cuartos[1].text.strip()
                        print(f"Segundo Cuarto: {numero5}")
                
                # Extract Quinto (5th prizes - 8 prizes) - class p5
                p5 = lottery_container.find('li', class_='p5')
                if p5:
                    quintos = p5.find_all('span')
                    quinto_nums = [numero6, numero7, numero8, numero9, numero10, numero11, numero12, numero13]
                    for i, span in enumerate(quintos):
                        if i < 8 and span.text.strip():
                            quinto_nums[i] = span.text.strip()
                            print(f"Quinto {i+1}: {quinto_nums[i]}")
                    
                    numero6, numero7, numero8, numero9, numero10, numero11, numero12, numero13 = quinto_nums
                
                print("Successfully extracted lottery numbers")
            else:
                print("Lottery container not found - prizes may not be drawn yet")
            
        else:
            print(f"Failed to fetch webpage. Status code: {response.status_code}")
            error = 1
            
    except Exception as e:
        print(f"Error parsing webpage: {str(e)}")
        error = 1
    
    # Create dictionary with results
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
    
    return premios

if __name__ == "__main__":
    # Parse the webpage
    result = parse_rtve_loteria_resumen()
    
    # Get the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = script_dir + "/output"
    
    print(script_dir)
    
    # Specify the file path
    output_file = os.path.join(script_dir, jsonFileName)
    
    print(output_file)
    
    # Save to JSON file
    create_json_file(result, output_file)
    
    print(f"Data saved to {output_file}")
    print(f"Results: {result}")
