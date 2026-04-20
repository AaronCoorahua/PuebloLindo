Esto es para guiar a la IA, no es parte del entregable.

## Plan: MVP Backend WhatsApp + KAPSO (Sin IA)

Diseñar un backend FastAPI mínimo y funcional para tickets vía WhatsApp con KAPSO, sin lógica de IA. El objetivo es asegurar un flujo end-to-end estable: webhook entrante -> persistencia ticket/mensaje -> respuesta automática al usuario -> consulta de tickets por API. Se prioriza simplicidad, idempotencia y contrato claro para implementación rápida.

**Steps**
1. Fase 1 - Alcance y contrato de integración KAPSO
1. Confirmar alcance explícito: sin IA, sin clasificación automática, sin orquestación compleja.
2. Definir endpoint de webhook `POST /api/v1/webhooks/whatsapp` con respuesta rápida `200`/`202` y body simple de ACK.
3. Definir endpoint de salida `POST /api/v1/messages/send` para enviar mensajes vía API de KAPSO.
4. Definir tiempos de respuesta del webhook: objetivo <2s para evitar reintentos agresivos del proveedor.

2. Fase 2 - Estructura de proyecto (monolito modular)
1. Mantener arquitectura por módulo y separación de responsabilidades: `router.py`, `schemas.py`, `service.py`.
2. Crear módulos backend:
   - `app/modules/webhooks` (entrada WhatsApp)
   - `app/modules/messages` (salida a KAPSO)
   - `app/modules/tickets` (consulta y cierre)
3. Crear capa de persistencia simple para MVP:
   - `app/models` (entidades DB)
   - `app/repositories` (operaciones DB mínimas)
4. Crear clientes externos y utilidades:
   - `app/integrations/kapso_client.py`
   - `app/core/idempotency.py`
   - `app/core/logging.py`

3. Fase 3 - Definición exacta de endpoints
1. `POST /api/v1/webhooks/whatsapp`
   - Request (normalizado): `phone`, `message`, `external_message_id`, `timestamp`, `channel`.
   - Respuesta: `{"received": true, "event_id": "..."}`.
   - Acción: validar payload, aplicar idempotencia por `external_message_id`, crear ticket si no existe ticket abierto del phone, guardar mensaje `sender=user`, disparar auto-reply.
2. `POST /api/v1/messages/send`
   - Request: `phone`, `message`.
   - Respuesta: `{"sent": true, "provider_message_id": "..."}` o error controlado.
   - Acción: llamar KAPSO (real o mock), registrar mensaje `sender=system` asociado al ticket.
3. `GET /api/v1/tickets`
   - Query opcional: `status`, `limit`, `cursor` (o `offset`).
   - Respuesta: lista de tickets paginada.
4. `GET /api/v1/tickets/{id}`
   - Respuesta: detalle de ticket + mensajes ordenados por fecha.
5. `POST /api/v1/tickets/{id}/close`
   - Respuesta: ticket actualizado a `closed`.

4. Fase 4 - Schemas Pydantic (precisos)
1. Dominio Ticket
   - `id: UUID`
   - `user_phone: str`
   - `status: Literal["open", "closed"]`
   - `created_at: datetime`
   - `updated_at: datetime`
2. Dominio Message
   - `id: UUID`
   - `ticket_id: UUID`
   - `external_message_id: str | None`
   - `sender: Literal["user", "system"]`
   - `content: str`
   - `created_at: datetime`
3. Contratos API
   - `WebhookWhatsAppIn`
   - `WebhookAckOut`
   - `SendMessageIn`
   - `SendMessageOut`
   - `TicketListOut`
   - `TicketDetailOut`
   - `CloseTicketOut`

5. Fase 5 - Payload mock KAPSO y mapeo
1. Definir payload mock de referencia para desarrollo local:
   - `event: "message.received"`
   - `message_id: "kapso-msg-123"`
   - `from: "+51999111222"`
   - `text: "hola"`
   - `timestamp: "2026-04-19T21:00:00Z"`
2. Definir mapper robusto de payload proveedor -> schema interno, con validación y defaults seguros.
3. Registrar body crudo en logs estructurados para debugging (sin secretos).

6. Fase 6 - Idempotencia y reglas de negocio mínimas
1. Idempotencia por `external_message_id` (unique index en DB).
2. Si llega webhook repetido: no duplicar ticket ni mensaje; responder ACK exitoso.
3. Regla de ticket:
   - Si existe ticket `open` para `user_phone`, reutilizarlo.
   - Si no existe, crear ticket nuevo `open`.
4. Auto-reply fijo MVP (sin IA): `Hemos recibido tu mensaje. Te contactaremos pronto.`

7. Fase 7 - Flujo funcional completo (hello world)
1. WhatsApp user envía "hola".
2. KAPSO llama webhook.
3. Backend persiste ticket y mensaje.
4. Backend llama servicio `messages/send`.
5. KAPSO entrega respuesta al usuario.
6. `GET /api/v1/tickets` y `GET /api/v1/tickets/{id}` reflejan datos persistidos.

8. Fase 8 - Verificación de implementación
1. Prueba manual webhook con payload mock (curl/Postman) y validar ACK.
2. Verificar creación de ticket y mensaje en DB.
3. Verificar no duplicación al reenviar mismo `external_message_id`.
4. Verificar envío saliente con mock/reales de KAPSO.
5. Verificar consulta de tickets y cierre de ticket.

**Relevant files**
- `backend/app/main.py` - registrar routers de `webhooks`, `messages`, `tickets`.
- `backend/app/core/config.py` - variables `KAPSO_BASE_URL`, `KAPSO_API_KEY`, `KAPSO_WEBHOOK_SECRET`, `AUTO_REPLY_TEXT`.
- `backend/app/modules/webhooks/router.py` - endpoint `POST /webhooks/whatsapp`.
- `backend/app/modules/webhooks/schemas.py` - contratos de entrada/salida del webhook.
- `backend/app/modules/webhooks/service.py` - orquestación webhook + idempotencia + ticket.
- `backend/app/modules/messages/router.py` - endpoint `POST /messages/send`.
- `backend/app/modules/messages/service.py` - envío por cliente KAPSO.
- `backend/app/modules/tickets/router.py` - `GET /tickets`, `GET /tickets/{id}`, `POST /tickets/{id}/close`.
- `backend/app/modules/tickets/schemas.py` - schemas de ticket y message para API.
- `backend/app/models/ticket.py` - entidad Ticket.
- `backend/app/models/message.py` - entidad Message.
- `backend/app/repositories/tickets_repository.py` - lectura/escritura tickets.
- `backend/app/repositories/messages_repository.py` - lectura/escritura mensajes.
- `backend/app/integrations/kapso_client.py` - cliente HTTP a KAPSO (mockable).
- `backend/README.md` o `README.md` - guía de prueba rápida del flujo WhatsApp.

**Verification**
1. Ejecutar backend local y confirmar `/docs` con los 5 endpoints definidos.
2. Simular webhook válido y verificar respuesta `received=true`.
3. Confirmar en DB: 1 ticket + 1 mensaje `sender=user` + 1 mensaje `sender=system`.
4. Repetir webhook con mismo `external_message_id` y confirmar idempotencia (sin duplicados).
5. Consultar `GET /tickets` con filtro `status=open` y paginación.
6. Consultar `GET /tickets/{id}` y validar lista de mensajes.
7. Ejecutar `POST /tickets/{id}/close` y validar transición de estado.

**Decisions**
- Incluido: integración KAPSO (webhook + envío), ticketing básico, persistencia, idempotencia, logging estructurado.
- Excluido: IA, clasificación automática, enrutar por prioridad, async workers avanzados, analítica compleja.
- Base de datos para MVP: la ya definida por el proyecto (Supabase/Postgres), con índices únicos para idempotencia.
- Política de respuesta webhook: ACK rápido y lógica mínima para robustez frente a reintentos.

**Further Considerations**
1. Si KAPSO usa firma HMAC, validar firma en `POST /webhooks/whatsapp` antes de procesar payload.
2. Si KAPSO no garantiza `message_id` único, construir key de idempotencia compuesta (`phone + timestamp + hash(text)`) como respaldo.
3. Mantener endpoint `POST /messages/send` reutilizable para mensajes manuales de soporte además del auto-reply.