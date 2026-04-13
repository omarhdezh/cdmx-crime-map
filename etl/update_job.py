import urllib.request
import os
import pandas as pd
from datetime import datetime

# URLs base del Portal de Datos Abiertos CDMX
BASE_URL = "https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_DATA_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "data"))
CLEAN_FILE = os.path.join(LOCAL_DATA_DIR, "carpetas_limpio.csv")

def update_data():
    print("Iniciando Job de Actualización de Datos...")
    
    # Intentar descargar el acumulado más reciente (2025_01)
    # Patrón: carpetasFGJ_acumulado_2025_01.csv
    target_file = "carpetasFGJ_acumulado_2025_01.csv"
    url = BASE_URL + target_file
    local_path = os.path.join(LOCAL_DATA_DIR, target_file)
    
    if not os.path.exists(LOCAL_DATA_DIR):
        os.makedirs(LOCAL_DATA_DIR)

    print(f"Verificando conexión con: {url}")
    try:
        # Descargar archivo si no existe
        if not os.path.exists(local_path):
            print(f"Descargando nuevo set de datos ({target_file})...")
            urllib.request.urlretrieve(url, local_path)
            print("Descarga completada.")
        else:
            print("El archivo ya existe localmente. Procesando...")

        # Procesar y limpiar para la app
        print("Limpiando y normalizando datos...")
        df = pd.read_csv(local_path, low_memory=False)
        
        # Columnas necesarias para la app
        needed = [
            "fecha_hecho", "delito", "categoria_delito", "alcaldia_hecho", 
            "colonia_hecho", "latitud", "longitud", "alcaldia_catalogo", "colonia_catalogo"
        ]
        
        # Procesar
        df = df[needed].copy()
        
        # Extraer año y filtrar por 2024+
        df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")
        df["anio"] = df["fecha_hecho"].dt.year
        df = df[df["anio"] >= 2024].copy()
        
        # Aplicar Title Case (Camel Case para visualización)
        df["alcaldia_hecho"] = df["alcaldia_hecho"].str.title()
        if "alcaldia_catalogo" in df.columns:
            df["alcaldia_catalogo"] = df["alcaldia_catalogo"].str.title()
        
        if "colonia_hecho" in df.columns:
            df["colonia_hecho"] = df["colonia_hecho"].str.title()
        if "colonia_catalogo" in df.columns:
            df["colonia_catalogo"] = df["colonia_catalogo"].str.title()

        # Eliminar nulos en ubicación
        df.dropna(subset=["latitud", "longitud"], inplace=True)
        
        # Guardar el archivo limpio principal
        print(f"Guardando {len(df)} registros en {CLEAN_FILE}...")
        df.to_csv(CLEAN_FILE, index=False)
        print("Proceso finalizado con éxito.")
        
    except Exception as e:
        print(f"Error durante la actualización: {e}")

if __name__ == "__main__":
    update_data()
