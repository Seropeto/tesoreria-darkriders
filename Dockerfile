# Usamos una imagen ligera de Python
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# --- CORRECCIÓN AQUÍ ---
# Antes decía: COPY requirements.txt .
# Ahora debe decir explícitamente dónde está:
COPY backend/requirements.txt .

# Instalamos dependencias
RUN pip install --no-cache-dir -r requirements.txt

# --- AJUSTE DE RUTAS ---
# Copiamos el código del Backend a la raíz del contenedor
COPY backend /app

# Copiamos el Frontend dentro de la carpeta frontend
COPY frontend /app/frontend

# Puerto expuesto
EXPOSE 8000

# Comando de inicio
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]