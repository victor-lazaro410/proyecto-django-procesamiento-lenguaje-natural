# Módulo de N-gramas (Django)

Este paquete agrega generación de n-gramas (n > 1) a partir de tokens del preprocesamiento y muestra sus frecuencias.

## Endpoints
- **/ngrams/**: Vista HTML con formulario para ingresar texto y `n`. Muestra tabla de frecuencias.
- **/ngrams/api/** (POST, JSON): Calcula frecuencias desde `tokens` o `text`.
  - Cuerpo:
    ```json
    { "tokens": ["hola","mundo"], "n": 2 }
    ```
    o
    ```json
    { "text": "Hola mundo hola", "n": 2 }
    ```

## Integración con el flujo actual
La vista intenta usar una función `tokenize` existente del proyecto (por ejemplo `nlp.tokenize`, `preprocess.tokenize`, etc.).
Si no la encuentra, utiliza un tokenizador simple de respaldo.

## Instalación automática
Este ZIP ya incluye:
- App `ngram` añadida a `INSTALLED_APPS` en `settings.py`.
- Ruta `path('ngrams/', include('ngram.urls'))` añadida al `urls.py` raíz.

## Pruebas
Se incluyen pruebas unitarias en `ngram/tests/test_services.py` (pytest).
Ejecuta:
```
pytest -q
```

## Notas
- No se persisten resultados en DB; todo es en memoria.
- La app no rompe flujos existentes si no se usa.