# Prompt de arranque MVP

Rol: Actua como Tech Lead full-stack para un MVP de Customer Success.

Contexto:

- Proyecto: PuebloLindo (marketplace con tickets entrantes por WhatsApp).
- Stack objetivo: FastAPI + Supabase + Next.js.
- El flujo debe funcionar de extremo a extremo para demo tecnica.

Objetivo de esta iteracion:

- Implementar un pipeline basico: webhook entrante -> procesamiento de agente -> creacion/actualizacion de ticket -> visualizacion en dashboard.

Alcance:

1. Backend en backend/app/modules (webhooks, agent, tickets, messages).
2. Frontend en frontend/app y frontend/src/features/tickets.
3. Persistencia solo en Supabase (sin sqlite fallback).

Restricciones:

1. Mantener idempotencia por external_message_id.
2. Mantener rutas consistentes bajo /api/v1.
3. No bloquear demo por falta de credenciales externas: permitir modo mock donde aplique.

Criterios de aceptacion:

1. Un webhook valido debe devolver ack y registrar el evento.
2. Debe existir ticket abierto visible en dashboard.
3. El flujo debe soportar create o update segun contexto.

Salida esperada del asistente:

1. Lista de archivos a tocar.
2. Cambios minimos por modulo.
3. Checklist de validacion manual.

# Resultado observado

Buen prompt para desbloquear el MVP end-to-end sin sobre-disenar.
