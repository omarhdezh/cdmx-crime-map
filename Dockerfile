# Usar imagen base ligera de Python
FROM python:3.11-slim

# Evitar que Python genere archivos .pyc y asegurar que el log se vea en tiempo real
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Crear directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias para Pandas/Numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código (incluyendo api, etl y data)
COPY . .

# Crear la carpeta de datos si no existe
RUN mkdir -p data

# Exponer el puerto de FastAPI
EXPOSE 8000

# Comando para correr la API (usando el host 0.0.0.0 para que sea accesible desde fuera)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
