import requests
from bs4 import BeautifulSoup
import json
import os
import re

my_dictionary = {}

jsonFileName = "LoteriaElNino.json"

urls = [
    "https://www.rtve.es/loterias/loteria-nino/Loteria_00000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_05000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_10000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_15000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_20000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_25000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_30000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_35000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_40000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_45000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_50000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_55000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_60000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_65000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_70000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_75000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_80000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_85000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_90000.shtml",
    "https://www.rtve.es/loterias/loteria-nino/Loteria_95000.shtml",
]

statusCode = "0"

my_dictionary["status"] = statusCode

def create_json_file(data, filename):
    with open(filename, 'w') as file:
        json.dump(data, file, indent=2)
        file.write('\n')

def parse_loteria_webpage(url):
    # Disable SSL verification (use with caution)
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    # Fetch the HTML content of the webpage
    response = requests.get(url, verify=False)
    
    if response.status_code == 200:
        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the table containing the information
        table = soup.find('table', id='millares')
        
        if table:
            # Extract table rows
            rows = table.find_all('tr')
            
            # Extract table headers
            headers = [header.text.strip() for header in rows[0].find_all('th')]
            
            # Extract table data
            data = []
            
            for row in rows[1:]:
                row_data = [td.text.strip() for td in row.find_all('td')]
                if len(row_data) > 1:
                   
                    if my_dictionary.get(row_data[0]) is not None:
                        print("Key exists in the dictionary. Do nothing")
                    else:
                        #print("Key does not exist in the dictionary. Add it")
                        sanitised1 = row_data[0].replace(".", "")
                        sanitised1 = sanitised1.replace("€", "")
                        sanitised1 = sanitised1.replace("\u20ac", "")
                        sanitised2 = row_data[2].replace(".", "")
                        sanitised2 = sanitised2.replace("€", "")
                        sanitised2 = sanitised2.replace("\u20ac", "")
                        my_dictionary[sanitised1] = sanitised2
                        #print(my_dictionary)
                        #data.append(my_dictionary)

                elif len(row_data) == 1:
                    parts = row_data[0].split()
                    part1 = parts[0]
                    part2 = parts[1]
                    sanitised1 = part1.replace(".", "")
                    sanitised1 = sanitised1.replace("º", "")
                    sanitised1 = sanitised1.replace("\u20ac", "")
                    sanitised1 = re.sub(r'\D', '', sanitised1)
                    sanitised1 = sanitised1[:5]
                    sanitised2 = part2.replace(".", "")
                    sanitised2 = sanitised2.replace("€", "")
                    sanitised2 = sanitised2.replace("\u20ac", "")
                    sanitised2 = sanitised2.replace("Premio", "")

                    my_dictionary[sanitised1] = sanitised2
                    
            # Convert the data to JSON
            #json_data = json.dumps(data, ensure_ascii=False, indent=2)
            
            return my_dictionary
        else:
            print("Table not found on the webpage.")
    else:
        print(f"Failed to fetch the webpage. Status code: {response.status_code}")

if __name__ == "__main__":

    for url in urls:
        result = parse_loteria_webpage(url)
    
    if result:
        # Get the script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_dir = script_dir + "/output"

        print(script_dir)

        # Specify the file path
        output_file = os.path.join(script_dir, jsonFileName)

        print(output_file)

        # Provide the dictionary and file path
        create_json_file(my_dictionary, output_file)

