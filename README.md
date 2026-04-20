# Pueblo Lindo

Pueblo Lindo es un MVP de triage para Customer Success: recibe mensajes de WhatsApp, clasifica por area, crea/actualiza tickets y los muestra en un dashboard Kanban.

## Produccion (demo activa)

- Web desplegada: https://pueblo-lindo.vercel.app
- Numero de WhatsApp para probar al agente: +1 (201) 331-5463
- Nota sobre Gemini: si te aparece un mensaje indicando que Gemini no responde, normalmente es por limites de free tier. Puedes escribirme y cambio la API key rapidamente para continuar la prueba.

## 4 flujos sugeridos para probar por WhatsApp

### Flujo 1 - Venta no reflejada (intake + confirmacion)

Mensajes sugeridos:

1. Hola, tengo un problema con una venta.
2. Soy comprador, pedido A12345, me cobraron y no aparece la venta.
3. SI

Resultado esperado:

- El agente primero pide datos faltantes.
- Cuando supera umbral, pide confirmacion.
- Solo crea ticket despues de responder SI.

### Flujo 2 - Pago rechazado

Mensajes sugeridos:

1. No puedo pagar, me rechaza la tarjeta.
2. Transaccion TX-778812, metodo tarjeta visa, me sale error de pago.
3. SI

Resultado esperado:

- El caso se enruta a pagos.
- Se pide/usa referencia de transaccion.
- Se confirma antes de crear ticket.

### Flujo 3 - Envio demorado

Mensajes sugeridos:

1. Mi envio esta demorado.
2. Guia TRK-556001, courier X, no llega desde hace 5 dias.
3. SI

Resultado esperado:

- El caso cae en envios.
- El agente incluye referencia y contexto de envio.
- Crea ticket solo tras confirmacion.

### Flujo 4 - Cancelar antes de crear ticket

Mensajes sugeridos:

1. Tengo un reclamo por una compra.
2. Es urgente, pedido RQ-11223.
3. cancelar

Resultado esperado:

- El agente limpia la sesion de intake.
- No se crea ticket.
- Se puede reiniciar el flujo luego con un nuevo mensaje.

## Arquitectura

- Frontend: Next.js 16 + TypeScript.
- Backend: FastAPI + Supabase.
- Canal: Kapso (WhatsApp).
- LLM: Gemini (con fallback de modelo).

## Levantar el proyecto en local (paso a paso)

### 1) Requisitos

- Python 3.12
- Node.js 20+
- Proyecto en Supabase
- Cuenta Kapso con numero conectado (si probaras envio real por WhatsApp)

### 2) Clonar y entrar al repo

```powershell
git clone <tu-repo>
cd PuebloLindo
```

### 3) Configurar Supabase primero

1. Crea un proyecto en Supabase.
2. Entra a Project Settings > API.
3. Copia:
	 - Project URL -> SUPABASE_URL
	 - Service role key -> SUPABASE_KEY
4. En SQL Editor, ejecuta el script [backend/sql/supabase_schema.sql](backend/sql/supabase_schema.sql).

### 4) Configurar backend

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita backend/.env con estas variables (minimo):

```dotenv
APP_NAME=PuebloLindo API
API_V1_PREFIX=/api/v1
FRONTEND_ORIGIN=http://localhost:3000

SUPABASE_URL=https://<tu-proyecto>.supabase.co
SUPABASE_KEY=<service_role_key>
SUPABASE_SCHEMA=public
SUPABASE_TICKETS_TABLE=tickets
SUPABASE_MESSAGES_TABLE=messages

KAPSO_BASE_URL=https://api.kapso.ai/meta/whatsapp/v24.0
KAPSO_API_KEY=
KAPSO_PHONE_NUMBER_ID=
KAPSO_SEND_PATH=/{phone_number_id}/messages
KAPSO_MOCK_MODE=true

GEMINI_API_KEY=<tu_api_key_gemini>
GEMINI_MODEL_PRIMARY=gemini-3.1-flash-lite-preview
GEMINI_MODEL_FALLBACK=gemini-3-flash-preview

AUTO_REPLY_TEXT=Hemos recibido tu mensaje. Te contactaremos pronto.
```

Notas importantes:

- GEMINI_API_KEY: para clasificacion con LLM en local.
- KAPSO_MOCK_MODE=true: permite pruebas locales sin credenciales reales de Kapso.
- Si vas a enviar mensajes reales por Kapso, cambia KAPSO_MOCK_MODE=false y completa KAPSO_API_KEY + KAPSO_PHONE_NUMBER_ID.

### 5) Ejecutar backend

```powershell
cd backend
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

Backend disponible en:

- http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

### 6) Configurar y ejecutar frontend

```powershell
cd frontend
npm install
Copy-Item .env.example .env
```

Edita frontend/.env:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
FRONTEND_ACCESS_PIN=1234
```

Ejecuta:

```powershell
cd frontend
npm run dev
```

Frontend disponible en:

- http://localhost:3000
- Dashboard principal redirige a /home

## Configurar Kapso (paso a paso)

### 1) Conectar numero de WhatsApp en Kapso

1. Ingresa a tu cuenta de Kapso.
2. Crea o abre tu canal de WhatsApp.
3. Completa onboarding para conectar el numero (sandbox o numero productivo).
4. Verifica que el numero quede en estado activo.

### 2) Obtener credenciales

1. Copia la API key de Kapso.
2. Copia el Phone Number ID del numero conectado.
3. Configura en backend/.env:

```dotenv
KAPSO_API_KEY=<kapso_api_key>
KAPSO_PHONE_NUMBER_ID=<phone_number_id>
KAPSO_MOCK_MODE=false
```

### 3) Configurar webhook hacia este backend

URL de webhook del proyecto:

- POST /api/v1/webhooks/whatsapp

Ejemplos:

- Produccion: https://<tu-backend>/api/v1/webhooks/whatsapp
- Local (con tunnel): https://<tu-tunnel>/api/v1/webhooks/whatsapp

Si pruebas local, levanta un tunnel (ejemplo ngrok):

```powershell
ngrok http 8000
```

Usa la URL https publica de ngrok en la configuracion de webhook de Kapso.

### 4) Verificacion rapida

Puedes validar salida de mensajes con:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/messages/send \
	-H "Content-Type: application/json" \
	-d '{"phone":"+12013315463","message":"Prueba de salida desde backend"}'
```

## Configurar Supabase (paso a paso)

### 1) Crear tablas e indices

Ejecuta completo [backend/sql/supabase_schema.sql](backend/sql/supabase_schema.sql) en SQL Editor.

Ese script crea y/o actualiza:

- Tabla public.tickets
- Tabla public.messages
- Indice idx_tickets_phone_status
- Indice idx_tickets_phone_status_activity
- Indice idx_messages_phone_created
- Indice unico parcial idx_messages_external_unique

### 2) SQL de referencia (extracto)

```sql
create table if not exists public.tickets (
	id uuid primary key,
	user_phone text not null,
	status text not null check (status in ('open', 'closed')),
	area text not null default 'otros',
	summary text not null default '',
	created_at timestamptz not null,
	updated_at timestamptz not null,
	last_activity_at timestamptz not null
);

create index if not exists idx_tickets_phone_status
	on public.tickets(user_phone, status);

create index if not exists idx_tickets_phone_status_activity
	on public.tickets(user_phone, status, last_activity_at desc);

create table if not exists public.messages (
	id uuid primary key,
	ticket_id uuid not null references public.tickets(id) on delete cascade,
	user_phone text not null,
	external_message_id text null,
	sender text not null check (sender in ('user', 'agent')),
	content text not null,
	created_at timestamptz not null
);

create index if not exists idx_messages_phone_created
	on public.messages(user_phone, created_at desc);

create unique index if not exists idx_messages_external_unique
	on public.messages(external_message_id)
	where external_message_id is not null;
```

### 3) Script opcional de limpieza

Si quieres eliminar persistencia de mensajes, revisa [backend/sql/drop_messages_table.sql](backend/sql/drop_messages_table.sql).

## Endpoints principales

- GET /
- GET /health
- POST /api/v1/webhooks/whatsapp
- POST /api/v1/messages/send
- GET /api/v1/tickets
- GET /api/v1/tickets/{ticket_id}
- POST /api/v1/tickets/{ticket_id}/close
- POST /api/v1/agent/process

## Flujo de desarrollo recomendado

1. Cambiar backend (router/schemas/service).
2. Exportar OpenAPI:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts/export_openapi.py
```

3. Regenerar tipos frontend:

```powershell
cd frontend
npm run gen:api
```

4. Ajustar componentes y hooks del dashboard.