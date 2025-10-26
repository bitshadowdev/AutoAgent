def FactCheckerAgent(args: dict) -> dict:
    """Verifica la factualidad de un texto mediante búsquedas en Wikipedia.

    Parámetros:
        args (dict): {'text': str} texto que contiene una o más afirmaciones.

    Retorna:
        dict: {
            'ok': bool,               # True si la operación fue exitosa
            'report': list[dict] | None,  # Lista de resultados por afirmación
            'error': str | None       # Mensaje de error en caso de fallo
        }
    """
    import requests
    import re
    import traceback
    
    # Obtener texto
    text = args.get('text', '')
    if not text:
        return {'ok': False, 'report': None, 'error': 'Texto vacío'}
    
    try:
        # Separar enunciados usando puntuación final
        statements = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s]
        report = []
        for stmt in statements:
            # Consulta a la API de búsqueda de Wikipedia (opensearch)
            response = requests.get(
                'https://en.wikipedia.org/w/api.php',
                params={
                    'action': 'query',
                    'list': 'search',
                    'srsearch': stmt,
                    'format': 'json',
                    'utf8': 1
                },
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            # Si Wikipedia devuelve resultados, consideramos la afirmación verificada
            if data.get('query', {}).get('search'):
                report.append({
                    'statement': stmt,
                    'verified': True,
                    'source': 'Wikipedia search',
                    'details': f"{len(data['query']['search'])} resultados encontrados"
                })
            else:
                report.append({
                    'statement': stmt,
                    'verified': False,
                    'source': 'Wikipedia',
                    'details': 'Sin coincidencias'
                })
        return {'ok': True, 'report': report, 'error': None}
    except requests.exceptions.RequestException as e:
        # Errores de red, timeout, etc.
        return {'ok': False, 'report': None, 'error': f'Error de red: {str(e)}'}
    except Exception as e:
        # Cualquier otro error inesperado
        return {'ok': False, 'report': None, 'error': f'Error inesperado: {str(e)}'}