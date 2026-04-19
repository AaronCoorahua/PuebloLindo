# PuebloLindo

MVP con arquitectura frontend + backend desacoplada:

- `frontend`: Next.js (TypeScript, App Router).
- `backend`: FastAPI (Python 3.12) en monolito modular.
- Contrato API unico via OpenAPI.

## Estructura

```text
PuebloLindo/
	frontend/
		app/
		src/
			features/
			lib/api/
	backend/
		app/
			core/
			modules/
				health/
		scripts/
```

## Backend (FastAPI)

### Requisitos

- Python 3.12

### Instalacion

```powershell
cd backend
./.venv/Scripts/python.exe -m pip install -r requirements.txt
```

### Ejecutar

```powershell
cd backend
./.venv/Scripts/uvicorn.exe app.main:app --reload
```

### Endpoints MVP

- `GET /` -> `{"message": "Hello World"}`
- `GET /health` -> `{"status": "ok"}`
- `GET /docs` -> Swagger UI

### Exportar contrato OpenAPI

```powershell
cd backend
./.venv/Scripts/python.exe scripts/export_openapi.py
```

Genera `backend/openapi.json`.

## Frontend (Next.js)

### Requisitos

- Node.js 20.9+

### Instalacion

```powershell
cd frontend
npm install
```

### Generar tipos desde OpenAPI

```powershell
cd frontend
npm run gen:api
```

### Ejecutar

```powershell
cd frontend
npm run dev
```

## Flujo recomendado (MVP)

1. Cambiar backend (rutas/schemas/service).
2. Exportar OpenAPI (`backend/openapi.json`).
3. Regenerar cliente tipado en frontend (`npm run gen:api`).
4. Ajustar `api.ts` y `hooks.ts` de la feature correspondiente.