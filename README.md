First commit


## API de predição + frontend

API (FastAPI), a partir da raiz do repo:

```bash
pip install -r requirements.txt -r api/requirements.txt
uvicorn api.main:app --reload --port 8000   # docs em http://localhost:8000/docs
pytest api/test_api.py
```

Frontend (Next.js + TypeScript):

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev   # http://localhost:3000
```

## Deploy em Produção

### 1. API (Render.com - Gratuito e linkado ao GitHub)
1. Acesse [render.com](https://render.com) e entre com sua conta do GitHub.
2. Clique em **New +** > **Web Service**.
3. Selecione o repositório `ml-senac-grupo2`.
4. O Render detectará o arquivo `render.yaml` automaticamente (ou selecione runtime Python 3, Build Command: `pip install -r requirements.txt -r api/requirements.txt` e Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`).
5. Escolha o plano **Free** e clique em **Create Web Service**.
6. Copie a URL gerada (ex: `https://api-predicao-imoveis.onrender.com`).

### 2. Frontend (Vercel - Gratuito e linkado ao GitHub)
1. Acesse [vercel.com](https://vercel.com) e importe o repositório `ml-senac-grupo2`.
2. Em **Root Directory**, selecione a pasta `frontend`.
3. Em **Environment Variables**, adicione:
   - `NEXT_PUBLIC_API_URL` com o valor da URL do Render (ex: `https://api-predicao-imoveis.onrender.com`).
4. Clique em **Deploy**.