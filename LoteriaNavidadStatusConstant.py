"""
Lottery Status Constants
Centralized status management for Lotería de Navidad scripts

Status Codes:
0: El sorteo no ha comenzado aún. Todos los números aparecerán como no premiados.
1: El sorteo ha empezado. La lista de números premiados se va cargando poco a poco. 
   Un número premiado podría llegar a tardar unos minutos en aparecer.
2: El sorteo ha terminado y la lista de números y premios debería ser la correcta 
   aunque, tomada al oído, no podemos estar seguros de ella.
3: El sorteo ha terminado y existe una lista oficial en PDF.
4: El sorteo ha terminado y la lista de números y premios está basada en la oficial. 
   De todas formas, recuerda que la única lista oficial es la que publica la ONLAE 
   y deberías comprobar todos tus números contra ella.
"""

# Current status of the lottery draw
# Change this value to update the status across all scripts
LOTTERY_STATUS = 1

# Valid status codes
VALID_STATUSES = {0, 1, 2, 3, 4}

def get_status():
    """Returns the current lottery status"""
    return LOTTERY_STATUS

def validate_status(status_code):
    """Validates if a status code is valid"""
    return status_code in VALID_STATUSES

def get_status_description(status_code):
    """Returns the description for a given status code"""
    descriptions = {
        0: "El sorteo no ha comenzado aún",
        1: "El sorteo ha empezado",
        2: "El sorteo ha terminado (lista al oído)",
        3: "El sorteo ha terminado (lista oficial PDF disponible)",
        4: "El sorteo ha terminado (lista verificada con la oficial)"
    }
    return descriptions.get(status_code, "Estado desconocido")
