import pandas as pd
import numpy as np
import os

# URL directa del CSV más reciente
# URLs reales del Portal de Datos Abiertos CDMX (actualizadas)
# Archivo 2024 (41 MB, Jul 2024): carpetasFGJ_2024.csv
# Acumulado 2016-2024 (560 MB):  carpetasFGJ_acumulado_2025_01.csv
CSV_URL = "https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_2024.csv"
CSV_URL_ACUMULADO = "https://archivo.datos.cdmx.gob.mx/FGJ/carpetas/carpetasFGJ_acumulado_2025_01.csv"

def cargar_y_limpiar(url: str) -> pd.DataFrame:
    print(f"Descargando datos desde {url}...")
    try:
        df = pd.read_csv(url, low_memory=False)
    except Exception as e:
        print(f"Error al descargar, intentando con URL alternativa o archivo local: {e}")
        # Si falla podemos intentar con un archivo local o URL alternativa
        # Por ahora, simplemente relanzamos el error
        raise e

    print("Limpiando datos...")
    # Normalizar columnas a minúsculas
    df.columns = df.columns.str.lower().str.strip()

    # Eliminar filas sin coordenadas
    df = df.dropna(subset=["latitud", "longitud"])

    # Convertir a float
    df['latitud'] = pd.to_numeric(df['latitud'], errors='coerce')
    df['longitud'] = pd.to_numeric(df['longitud'], errors='coerce')
    df = df.dropna(subset=["latitud", "longitud"])

    # Filtrar coordenadas fuera de CDMX (bbox aproximado)
    df = df[
        (df["latitud"].between(19.05, 19.60)) &
        (df["longitud"].between(-99.40, -98.95))
    ]

    # Fecha como datetime
    df["fecha_hechos"] = pd.to_datetime(df["fecha_hechos"], errors="coerce")
    df["anio"] = df["fecha_hechos"].dt.year
    df["mes"]  = df["fecha_hechos"].dt.month

    # Normalizar texto
    for col in ["delito", "categoria_delito", "alcaldia_hechos", "colonia_hechos", "alcaldia_catalogo", "colonia_catalogo"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    # Si falta colonia_catalogo pero tenemos colonia_hechos
    if "colonia_catalogo" not in df.columns and "colonia_hechos" in df.columns:
        df["colonia_catalogo"] = df["colonia_hechos"]
    
    if "alcaldia_catalogo" not in df.columns and "alcaldia_hechos" in df.columns:
        df["alcaldia_catalogo"] = df["alcaldia_hechos"]

    return df

def agrupar_por_colonia(df: pd.DataFrame) -> pd.DataFrame:
    """Genera conteo de delitos por colonia y categoría — listo para la API."""
    return (
        df.groupby(["colonia_catalogo", "alcaldia_catalogo", "categoria_delito", "anio"])
        .agg(total=("latitud", "count"))
        .reset_index()
    )

def exportar_geojson_puntos(df: pd.DataFrame, path: str = "../mapa-delitos/public/delitos.geojson"):
    """Exporta una muestra de puntos para el heatmap de Leaflet."""
    # Ensure dir exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    sample = df.sample(min(50_000, len(df)), random_state=42)

    features = []
    for _, row in sample.iterrows():
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitud"], row["latitud"]]
            },
            "properties": {
                "delito": row.get("categoria_delito", ""),
                "anio": int(row.get("anio", 0)) if pd.notna(row.get("anio")) else 0,
                "colonia": row.get("colonia_catalogo", "")
            }
        })

    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)
    print(f"Exportado: {len(features)} puntos → {path}")

if __name__ == "__main__":
    # Asegurar que el directorio data/ existe
    os.makedirs("../data", exist_ok=True)
    
    df = cargar_y_limpiar(CSV_URL)
    print(f"Registros limpios: {len(df):,}")
    print(df["categoria_delito"].value_counts().head(10))
    
    # Exportar a CSV para el backend
    csv_path = "../data/carpetas_limpio.csv"
    print(f"Guardando {csv_path}...")
    df.to_csv(csv_path, index=False)
    
    # exportar_geojson_puntos(df)
    print("ETL Completado con éxito.")
