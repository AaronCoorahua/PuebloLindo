# Backend MVP - WhatsApp + KAPSO (sin IA)

Este backend implementa un flujo minimo funcional para tickets:

1. KAPSO envia webhook de mensaje entrante.
2. El backend crea/reutiliza ticket abierto.
3. El backend guarda mensaje del usuario.
4. El backend responde automaticamente al usuario.
5. Los tickets y mensajes se consultan por API.

## Endpoints

- `POST /api/v1/webhooks/whatsapp`
- `POST /api/v1/messages/send`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{id}`
- `POST /api/v1/tickets/{id}/close`

## Payload mock KAPSO

```json
{
  "event": "message.received",
  "message_id": "kapso-msg-123",
  "from": "+51999111222",
  "text": "hola",
  "timestamp": "2026-04-19T21:00:00Z",
  "channel": "whatsapp"
}
```

## Ejemplo rapido (curl)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/webhooks/whatsapp \
  -H "Content-Type: application/json" \
  -d '{"event":"message.received","message_id":"kapso-msg-123","from":"+51999111222","text":"hola","timestamp":"2026-04-19T21:00:00Z"}'
```

## Notas

- Idempotencia por `external_message_id`/`message_id`.
- Persistencia unicamente en Supabase.
- `KAPSO_MOCK_MODE=true` por defecto para pruebas sin credenciales reales.

## Configurar Supabase (bien)

Este backend usa Supabase como unica capa de persistencia.

Variables necesarias para Supabase (segun referencia oficial de supabase-py):

- `SUPABASE_URL`
- `SUPABASE_KEY`

Variables opcionales del proyecto:

- `SUPABASE_SCHEMA` (default `public`)
- `SUPABASE_TICKETS_TABLE` (default `tickets`)
- `SUPABASE_MESSAGES_TABLE` (default `messages`)

Pasos:

1. Instalar dependencias (`pip install -r requirements.txt`).
2. Completar `SUPABASE_URL` y `SUPABASE_KEY` en `.env`.
3. Ejecutar `backend/sql/supabase_schema.sql` en el SQL Editor de Supabase.

Si faltan `SUPABASE_URL` o `SUPABASE_KEY`, el backend falla al iniciar para evitar configuraciones incompletas.
