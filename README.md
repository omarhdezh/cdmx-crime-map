# 🇲🇽 CDMX Crime Map & INEGI Gap Analyzer

Un mapa interactivo y profesional de la incidencia delictiva en la Ciudad de México, que integra datos oficiales de la **FGJ-CDMX** y proyecciones de la **Cifra Negra del INEGI (ENVIPE 2024)**.

![Main View](screenshots/main_view.png)
*Vista Global de la CDMX con niveles de incidencia.*

![INEGI Gap Tooltip](screenshots/tooltip_view.png)
*Detalle de la Cifra Negra (INEGI) vs Denuncias Oficiales.*

![Neighborhood Drilldown](screenshots/neighborhood_view.png)
*Zoom hasta nivel de Colonia con sombreado de riesgo.*

---

## 🌟 Características principales

- **Visualización Granular**: Navega a niveles de Alcaldía.
- **Análisis de Cifra Negra**: Visualiza la brecha entre los delitos denunciados FGJ-CDMX y la realidad estimada según la ENVIPE 2024 del INEGI.
- **Internacionalización**: Soporte completo para Inglés y Español.
- **ETL Automatizado**: Scripts integrados para descargar y limpiar los datos más recientes del Portal de Datos Abiertos de la CDMX.
- **Diseño Premium**: Interfaz clara, profesional y responsiva (Mobile-First).

---

## 🏗️ Arquitectura del Proyecto

- **Front-end**: React + Leaflet (Mapas interactivos).
- **Back-end**: FastAPI (Python) + Pandas (Procesamiento de datos).
- **ETL**: Python scripts para automatización de datos.
- **Contenedores**: Docker.

---

## 🚀 Instalación Local

### Requisitos previos
- Python 3.11+
- Node.js 18+

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/cdmx-crime-map.git
cd cdmx-crime-map
```

### 2. Configurar el Back-end (API)
```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### 3. Configurar el Front-end
```bash
cd mapa-delitos
npm install
npm run dev
```

---

## 🛠️ Para Colaboradores y Desarrolladores

### Configuración del Admin Token
Para proteger el endpoint de actualización de datos en el servidor, este proyecto utiliza un `ADMIN_TOKEN`. 
- Si quieres contribuir o desplegar tu propia versión, asegúrate de configurar la variable `ADMIN_TOKEN` en tu archivo `.env`.
- Para disparar la actualización de datos desde la nube, visita: `https://tu-api.com/admin/update-data?token=TU_TOKEN_AQUÍ`.

> [!IMPORTANT]
> Nunca compartas tu token real en el repositorio. Usa el archivo `.env.example` como referencia para los nombres de las variables.

---

## 📄 Licencia
Este proyecto está bajo la licencia **MIT**. Los datos de incidencia delictiva pertenecen al Portal de Datos Abiertos de la Ciudad de México bajo la licencia **CC BY 4.0**.

---

## 🤝 Contribuciones
¡Las contribuciones son bienvenidas! Siéntete libre de abrir un *Issue* o enviar un *Pull Request*.

---

Creado por [Omar Hernandez](https://github.com/tu-usuario)
