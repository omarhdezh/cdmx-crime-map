import urllib.request
import json
import os

URL_COLONIAS = "https://datos.cdmx.gob.mx/dataset/02c6ce99-dbd8-47d8-aee1-ae885a12bb2f/resource/026b42d3-a609-44c7-a83d-22b2150caffc/download/catlogo-de-colonias.json"
OUT_FILE = os.path.join(os.path.dirname(__file__), "..", "mapa-delitos", "public", "colonias.json")

def download_and_simplify():
    print("🌍 Descargando catálogo de colonias...")
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    
    try:
        urllib.request.urlretrieve(URL_COLONIAS, OUT_FILE)
        print("✅ Descarga exitosa.")
        
        # Opcional: Simplificar o filtrar si es demasiado pesado
        with open(OUT_FILE, 'r') as f:
            data = json.load(f)
            
        print(f"🏘️ Total de colonias encontradas: {len(data.get('features', []))}")
        
        # Aquí podríamos filtrar para quedarnos solo con lo esencial: nombre y alcaldia
        # para reducir el tamaño del archivo si fuera necesario.
        # Por ahora lo dejaremos completo para asegurar fidelidad.
        
    except Exception as e:
        print(f"❌ Error descargando colonias: {e}")

if __name__ == "__main__":
    download_and_simplify()
