FROM python:3.12-slim

# Cria usuário não-root (requisito do Hugging Face Spaces: UID 1000)
RUN useradd -m -u 1000 user

WORKDIR /app

# Instala dependências do Python
COPY requirements.txt .
COPY api/requirements.txt api-requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -r api-requirements.txt

# Copia o código, encoders e modelo
COPY api/ api/
COPY data/ data/
COPY imoveis-modelo.pickle imoveis-modelo.pickle

# Dá permissão ao usuário
RUN chown -R user:user /app

USER user

# Hugging Face Spaces expõe a porta 7860
EXPOSE 7860

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "7860"]
