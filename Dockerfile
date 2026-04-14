# Usando a versão estável "bookworm" para evitar ferramentas "novas demais" que quebram o dlib
FROM python:3.10-slim-bookworm

WORKDIR /app

# Instalando dependências do sistema necessárias para dlib e face-recognition
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libx11-6 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip

# Definindo flag para o CMake aceitar a política de versões antigas do dlib
# E instalando as dependências
RUN CMAKE_ARGS="-DCMAKE_POLICY_VERSION_MINIMUM=3.5" pip install -r requirements.txt

# O Railway define a porta automaticamente na variável $PORT. 
# Usamos 8000 como fallback se você testar localmente.
ENV PORT=8000
EXPOSE ${PORT}

CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}