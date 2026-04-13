from fastapi import FastAPI, Query, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from functools import lru_cache
import os
from dotenv import load_dotenv
from etl.update_job import update_data

load_dotenv()

app = FastAPI(title="API Mapa Delictivo CDMX")

# Configurar CORS dinámico
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "super-secret-token")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Columnas reales del CSV 2024 de la FGJ:
# anio_hecho, mes_hecho, fecha_hecho, hora_hecho, delito, categoria_delito,
# colonia_hecho, colonia_catalogo, alcaldia_hecho, alcaldia_catalogo, latitud, longitud

@lru_cache(maxsize=1)
def get_df():
    data_path = os.getenv("DATA_PATH", "data/carpetas_limpio.csv")
    csv_path = os.path.join(os.path.dirname(__file__), "..", data_path)
    csv_path = os.path.normpath(csv_path)
    
    if not os.path.exists(csv_path):
        print(f"ERROR: No se encontró el archivo en {csv_path}")
        return pd.DataFrame(columns=[
            "fecha_hecho", "categoria_delito", "alcaldia_catalogo",
            "colonia_catalogo", "latitud", "longitud", "anio"
        ])
    df = pd.read_csv(csv_path, low_memory=False)
    df["fecha_hecho"] = pd.to_datetime(df["fecha_hecho"], errors="coerce")
    return df


@app.get("/heatmap")
def heatmap(
    anio: int = Query(2024, ge=2016, le=2025),
    categoria: str = Query("TODOS"),
    alcaldia: str = Query("TODAS"),
):
    df = get_df().copy()
    if df.empty:
        return {"total": 0, "puntos": []}

    # Filtrar por año (columna anio o extraer de fecha)
    if "anio" in df.columns:
        df = df[df["anio"] == anio]
    else:
        df = df[df["fecha_hecho"].dt.year == anio]

    if categoria != "TODOS":
        df = df[df["categoria_delito"] == categoria.upper()]

    if alcaldia != "TODAS":
        col = "alcaldia_catalogo" if "alcaldia_catalogo" in df.columns else "alcaldia_hecho"
        df = df[df[col] == alcaldia.upper()]

    puntos = df[["latitud", "longitud"]].dropna()
    sample_size = min(30_000, len(puntos))
    return {
        "total": len(puntos),
        "puntos": puntos.sample(sample_size, random_state=42).values.tolist() if sample_size > 0 else []
    }


@app.get("/colonias")
def por_colonia(anio: int = 2024):
    df = get_df().copy()
    if df.empty:
        return []

    col_anio = "anio" if "anio" in df.columns else None
    if col_anio:
        df = df[df["anio"] == anio]
    else:
        df = df[df["fecha_hecho"].dt.year == anio]

    col_colonia = "colonia_catalogo" if "colonia_catalogo" in df.columns else "colonia_hecho"
    col_alc = "alcaldia_catalogo" if "alcaldia_catalogo" in df.columns else "alcaldia_hecho"

    resumen = (
        df.groupby([col_colonia, col_alc])
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )
    resumen.columns = ["colonia_catalogo", "alcaldia_catalogo", "total"]
    return resumen.head(50).to_dict(orient="records")


@app.get("/tendencia")
def tendencia(colonia: str = Query(None)):
    df = get_df().copy()
    if df.empty:
        return []

    col_colonia = "colonia_catalogo" if "colonia_catalogo" in df.columns else "colonia_hecho"
    if colonia:
        df = df[df[col_colonia] == colonia.upper()]

    df["mes_anio"] = df["fecha_hecho"].dt.to_period("M").astype(str)
    serie = df.groupby("mes_anio").size().reset_index(name="total")
    return serie.tail(24).to_dict(orient="records")


@app.get("/categorias")
def categorias():
    df = get_df()
    if df.empty:
        return ["TODOS"]
    cats = sorted(df["categoria_delito"].dropna().unique().tolist())
    return ["TODOS"] + cats


@app.get("/alcaldias")
def alcaldias():
    df = get_df()
    if df.empty:
        return ["TODAS"]
    col = "alcaldia_catalogo" if "alcaldia_catalogo" in df.columns else "alcaldia_hecho"
    alcs = sorted(df[col].dropna().unique().tolist())
    return ["TODAS"] + alcs


@app.get("/alcaldias-stats")
def alcaldias_stats(
    anio: int = Query(2024, ge=2024, le=2026),
    categoria: str = Query("TODOS"),
):
    """Devuelve conteo de delitos por alcaldía con tier de color asignado."""
    df = get_df().copy()
    if df.empty:
        return []

    # Filtrar año y categoría
    df = df[df["anio"] == anio]

    if categoria != "TODOS":
        df = df[df["categoria_delito"] == categoria.upper()]

    # Usar alcaldia_hecho si catalogo está vacío
    col = "alcaldia_hecho"
    if "alcaldia_catalogo" in df.columns and df["alcaldia_catalogo"].notna().sum() > 0:
        col = "alcaldia_catalogo"
        
    resumen = (
        df.groupby(col)
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )
    resumen.columns = ["alcaldia", "total"]

    # Asignar tier de color basado en percentiles
    if len(resumen) > 0:
        max_val = resumen["total"].max()
        def get_tier(total):
            pct = total / max_val
            if pct >= 0.75:  return {"tier": 4, "label": "Muy alta",  "color": "#ef4444"}  # rojo
            if pct >= 0.50:  return {"tier": 3, "label": "Alta",      "color": "#f97316"}  # naranja
            if pct >= 0.25:  return {"tier": 2, "label": "Media",     "color": "#a855f7"}  # morado
            return              {"tier": 1, "label": "Baja",       "color": "#22c55e"}  # verde

        result = []
        for _, row in resumen.iterrows():
            tier_info = get_tier(row["total"])
            result.append({
                "alcaldia": row["alcaldia"],
                "total": int(row["total"]),
                **tier_info
            })
        return result
    return []
@app.get("/anios")
def get_anios():
    return [2026, 2025, 2024]


@app.get("/colonias-stats")
def colonias_stats(
    alcaldia: str,
    anio: int = Query(2024, ge=2024, le=2026),
    categoria: str = Query("TODOS"),
):
    """Devuelve estadísticas por colonia dentro de una alcaldía específica."""
    df = get_df().copy()
    if df.empty:
        return []

    # Filtrar por año y alcaldia
    df = df[df["anio"] == anio]
    
    col_alc = "alcaldia_catalogo" if "alcaldia_catalogo" in df.columns else "alcaldia_hecho"
    df = df[df[col_alc] == alcaldia.upper()]

    if categoria != "TODOS":
        df = df[df["categoria_delito"] == categoria.upper()]

    col_colonia = "colonia_catalogo" if "colonia_catalogo" in df.columns else "colonia_hecho"
    resumen = (
        df.groupby(col_colonia)
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )
    resumen.columns = ["colonia", "total"]

    # Asignar tier de color basado en percentiles locales (de la alcaldía)
    if not resumen.empty:
        max_val = resumen["total"].max()
        def get_tier(total):
            pct = total / max_val if max_val > 0 else 0
            if pct >= 0.75: return {"tier": 4, "color": "#ef4444"}
            if pct >= 0.50: return {"tier": 3, "color": "#f97316"}
            if pct >= 0.25: return {"tier": 2, "color": "#a855f7"}
            return             {"tier": 1, "color": "#22c55e"}

        result = []
        for _, row in resumen.iterrows():
            tier_info = get_tier(row["total"])
            result.append({
                "colonia": row["colonia"],
                "total": int(row["total"]),
                **tier_info
            })
        return result
    return []


@app.get("/admin/update-data")
async def trigger_update(background_tasks: BackgroundTasks, token: str = Query(None)):
    """Ejecuta el job de actualización de datos en segundo plano."""
    if token != ADMIN_TOKEN:
        raise HTTPException(status_code=403, detail="Token de administración inválido")
    
    background_tasks.add_task(update_data)
    return {"status": "Job de actualización iniciado en segundo plano", "info": "Esto puede tardar varios minutos."}


@app.get("/api-status")
def status():
    return {"status": "online", "data_path": os.getenv("DATA_PATH", "data/carpetas_limpio.csv")}
