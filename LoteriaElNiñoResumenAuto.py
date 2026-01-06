import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import time
import subprocess
from LoteriaElNiñoStatusConstant import get_status

jsonFileName = "LoteriaElNinoResumen.json"

# URL to parse
url = "https://www.rtve.es/loterias/loteria-nino/"

def create_json_file(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)
        file.write('\n')

def parse_rtve_loteria_nino_resumen():
    """
    Parse RTVE lottery El Niño page to extract the main prizes
    Returns a dictionary with the prizes or -1 if they haven't appeared yet
    """
    
    # Initialize default values (numbers not drawn yet)
    timestamp_now = int(datetime.now().timestamp())
    status = get_status()
    
    # Prizes
    Primer_premio = -1
    Segundo_Premio = -1
    Tercer_Premio = -1
    
    # 4 cifras (2 prizes)
    Extraccion_4_cifras_1 = -1
    Extraccion_4_cifras_2 = -1
    
    # 3 cifras (14 prizes)
    Extraccion_3_cifras_1 = -1
    Extraccion_3_cifras_2 = -1
    Extraccion_3_cifras_3 = -1
    Extraccion_3_cifras_4 = -1
    Extraccion_3_cifras_5 = -1
    Extraccion_3_cifras_6 = -1
    Extraccion_3_cifras_7 = -1
    Extraccion_3_cifras_8 = -1
    Extraccion_3_cifras_9 = -1
    Extraccion_3_cifras_10 = -1
    Extraccion_3_cifras_11 = -1
    Extraccion_3_cifras_12 = -1
    Extraccion_3_cifras_13 = -1
    Extraccion_3_cifras_14 = -1
    
    # 2 cifras (5 prizes)
    Extraccion_2_cifras_1 = -1
    Extraccion_2_cifras_2 = -1
    Extraccion_2_cifras_3 = -1
    Extraccion_2_cifras_4 = -1
    Extraccion_2_cifras_5 = -1
    
    # Reintegros (3 refunds)
    Reintegro_1 = 0
    Reintegro_2 = 0
    Reintegro_3 = 0
    
    try:
        # Disable SSL verification warnings (use with caution)
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
        
        # Fetch the HTML content of the webpage
        response = requests.get(url, verify=False, timeout=10)
        
        if response.status_code == 200:
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main lottery results container
            # The prizes are in <ol id="viewLoteria2026">
            lottery_container = soup.find('ol', id='viewLoteria2026')
            
            if lottery_container:
                print("Found lottery container, extracting prizes...")
                
                # Extract Primer premio (1st prize) - class p1
                p1 = lottery_container.find('li', class_='p1')
                if p1:
                    span = p1.find('span')
                    if span and span.text.strip():
                        Primer_premio = int(span.text.strip())
                        print(f"Primer Premio: {Primer_premio}")
                
                # Extract Segundo premio (2nd prize) - class p2
                p2 = lottery_container.find('li', class_='p2')
                if p2:
                    span = p2.find('span')
                    if span and span.text.strip():
                        Segundo_Premio = int(span.text.strip())
                        print(f"Segundo Premio: {Segundo_Premio}")
                
                # Extract Tercer premio (3rd prize) - class p3
                p3 = lottery_container.find('li', class_='p3')
                if p3:
                    span = p3.find('span')
                    if span and span.text.strip():
                        Tercer_Premio = int(span.text.strip())
                        print(f"Tercer Premio: {Tercer_Premio}")
                
                # Extract 4 cifras (4-digit prizes - 2 prizes) - class p4
                p4 = lottery_container.find('li', class_='p4')
                if p4:
                    cifras4 = p4.find_all('span')
                    if len(cifras4) >= 1 and cifras4[0].text.strip():
                        Extraccion_4_cifras_1 = int(cifras4[0].text.strip())
                        print(f"4 cifras 1: {Extraccion_4_cifras_1}")
                    if len(cifras4) >= 2 and cifras4[1].text.strip():
                        Extraccion_4_cifras_2 = int(cifras4[1].text.strip())
                        print(f"4 cifras 2: {Extraccion_4_cifras_2}")
                
                # Extract 3 cifras (3-digit prizes - 14 prizes) - class p5
                p5 = lottery_container.find('li', class_='p5')
                if p5:
                    cifras3 = p5.find_all('span')
                    cifras3_nums = [
                        Extraccion_3_cifras_1, Extraccion_3_cifras_2, Extraccion_3_cifras_3,
                        Extraccion_3_cifras_4, Extraccion_3_cifras_5, Extraccion_3_cifras_6,
                        Extraccion_3_cifras_7, Extraccion_3_cifras_8, Extraccion_3_cifras_9,
                        Extraccion_3_cifras_10, Extraccion_3_cifras_11, Extraccion_3_cifras_12,
                        Extraccion_3_cifras_13, Extraccion_3_cifras_14
                    ]
                    for i, span in enumerate(cifras3):
                        if i < 14 and span.text.strip():
                            cifras3_nums[i] = int(span.text.strip())
                            print(f"3 cifras {i+1}: {cifras3_nums[i]}")
                    
                    (Extraccion_3_cifras_1, Extraccion_3_cifras_2, Extraccion_3_cifras_3,
                     Extraccion_3_cifras_4, Extraccion_3_cifras_5, Extraccion_3_cifras_6,
                     Extraccion_3_cifras_7, Extraccion_3_cifras_8, Extraccion_3_cifras_9,
                     Extraccion_3_cifras_10, Extraccion_3_cifras_11, Extraccion_3_cifras_12,
                     Extraccion_3_cifras_13, Extraccion_3_cifras_14) = cifras3_nums
                
                # Extract 2 cifras (2-digit prizes - 5 prizes) - class p6
                p6 = lottery_container.find('li', class_='p6')
                if p6:
                    cifras2 = p6.find_all('span')
                    cifras2_nums = [
                        Extraccion_2_cifras_1, Extraccion_2_cifras_2, Extraccion_2_cifras_3,
                        Extraccion_2_cifras_4, Extraccion_2_cifras_5
                    ]
                    for i, span in enumerate(cifras2):
                        if i < 5 and span.text.strip():
                            cifras2_nums[i] = int(span.text.strip())
                            print(f"2 cifras {i+1}: {cifras2_nums[i]}")
                    
                    (Extraccion_2_cifras_1, Extraccion_2_cifras_2, Extraccion_2_cifras_3,
                     Extraccion_2_cifras_4, Extraccion_2_cifras_5) = cifras2_nums
                
                # Extract Reintegros (refunds - 3 prizes) - class p7
                p7 = lottery_container.find('li', class_='p7')
                if p7:
                    reintegros = p7.find_all('span')
                    reintegros_nums = [Reintegro_1, Reintegro_2, Reintegro_3]
                    for i, span in enumerate(reintegros):
                        if i < 3 and span.text.strip():
                            reintegros_nums[i] = int(span.text.strip())
                            print(f"Reintegro {i+1}: {reintegros_nums[i]}")
                    
                    Reintegro_1, Reintegro_2, Reintegro_3 = reintegros_nums
                
                print("Successfully extracted lottery numbers")
            else:
                print("Lottery container not found - prizes may not be drawn yet")
            
        else:
            print(f"Failed to fetch webpage. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error parsing webpage: {str(e)}")
    
    # Create dictionary with results
    premios = {
        'timestamp': timestamp_now,
        'status': status,
        'Primer_premio': Primer_premio,
        'Segundo_Premio': Segundo_Premio,
        'Tercer_Premio': Tercer_Premio,
        'Extraccion_4_cifras_1': Extraccion_4_cifras_1,
        'Extraccion_4_cifras_2': Extraccion_4_cifras_2,
        'Extraccion_3_cifras_1': Extraccion_3_cifras_1,
        'Extraccion_3_cifras_2': Extraccion_3_cifras_2,
        'Extraccion_3_cifras_3': Extraccion_3_cifras_3,
        'Extraccion_3_cifras_4': Extraccion_3_cifras_4,
        'Extraccion_3_cifras_5': Extraccion_3_cifras_5,
        'Extraccion_3_cifras_6': Extraccion_3_cifras_6,
        'Extraccion_3_cifras_7': Extraccion_3_cifras_7,
        'Extraccion_3_cifras_8': Extraccion_3_cifras_8,
        'Extraccion_3_cifras_9': Extraccion_3_cifras_9,
        'Extraccion_3_cifras_10': Extraccion_3_cifras_10,
        'Extraccion_3_cifras_11': Extraccion_3_cifras_11,
        'Extraccion_3_cifras_12': Extraccion_3_cifras_12,
        'Extraccion_3_cifras_13': Extraccion_3_cifras_13,
        'Extraccion_3_cifras_14': Extraccion_3_cifras_14,
        'Extraccion_2_cifras_1': Extraccion_2_cifras_1,
        'Extraccion_2_cifras_2': Extraccion_2_cifras_2,
        'Extraccion_2_cifras_3': Extraccion_2_cifras_3,
        'Extraccion_2_cifras_4': Extraccion_2_cifras_4,
        'Extraccion_2_cifras_5': Extraccion_2_cifras_5,
        'Reintegro_1': Reintegro_1,
        'Reintegro_2': Reintegro_2,
        'Reintegro_3': Reintegro_3
    }
    
    return premios

if __name__ == "__main__":
    # Parse the webpage
    result = parse_rtve_loteria_nino_resumen()
    
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
