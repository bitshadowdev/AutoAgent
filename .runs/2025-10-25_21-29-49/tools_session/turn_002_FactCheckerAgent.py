import requests
import json
import re
import urllib.parse
from typing import Dict, Any

def FactCheckerAgent(args: Dict[str, Any]) -> Dict[str, Any]:
    """Verifica la factualidad de una respuesta textual.

    Parámetros:
        args: dict con la clave 'text' que contiene la respuesta a evaluar.

    Retorno:
        dict con los campos:
            - ok (bool): True si la verificación se realizó sin errores críticos.
            - report (list): Lista de dicts por afirmación encontrada con:
                * statement (str): la afirmación evaluada.
                * status (str): 'VERIFIED', 'FALSE', o 'UNKNOWN'.
                * source (str): URL de la fuente utilizada (Wikipedia) o None.
                * evidence (str): fragmento de texto que respalda la evaluación.
            - error (str, opcional): Mensaje de error en caso de fallo.
    """
    try:
        text = args.get('text', '')
        if not text:
            return {'ok': False, 'error': 'Texto vacío proporcionado.'}

        # Dividir el texto en oraciones simples (muy básico)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        report = []
        session = requests.Session()
        session.headers.update({'User-Agent': 'FactCheckerAgent/1.0 (https://github.com/openai)'})
        for sentence in sentences:
            statement = sentence.strip()
            if not statement:
                continue
            # Usar la primera frase significativa como query a Wikipedia
            query = statement.split(',')[0]
            query = query[:200]  # limitar longitud
            encoded = urllib.parse.quote(query)
            url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}'
            try:
                resp = session.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    # Comprobar si la frase está contenida en el extracto de Wikipedia
                    extract = data.get('extract', '').lower()
                    if statement.lower() in extract:
                        status = 'VERIFIED'
                    else:
                        # Si no coincide exactamente, buscar coincidencias parciales de palabras clave
                        words = set(re.findall(r"\w+", statement.lower()))
                        extract_words = set(re.findall(r"\w+", extract))
                        overlap = words.intersection(extract_words)
                        # Si la superposición es > 60% consideramos verificado de forma heurística
                        if words and len(overlap) / len(words) > 0.6:
                            status = 'VERIFIED'
                        else:
                            status = 'UNKNOWN'
                    source = data.get('content_urls', {}).get('desktop', {}).get('page')
                    evidence = data.get('extract', '')
                elif resp.status_code == 404:
                    status = 'UNKNOWN'
                    source = None
                    evidence = ''
                else:
                    # Otros códigos de error se tratan como fallo de red
                    return {'ok': False, 'error': f'Error HTTP {resp.status_code} al consultar Wikipedia.'}
            except requests.exceptions.RequestException as e:
                return {'ok': False, 'error': f'Error de red al consultar Wikipedia: {str(e)}'}

            report.append({
                'statement': statement,
                'status': status,
                'source': source,
                'evidence': evidence
            })
        return {'ok': True, 'report': report}
    except Exception as e:
        return {'ok': False, 'error': f'Excepción inesperada: {str(e)}'}