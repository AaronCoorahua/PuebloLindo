# Prompt de tono conversacional

Rol: Actua como Conversation Designer para soporte por WhatsApp.

Contexto:

- El bot ya clasifica y gestiona tickets, pero su tono se percibe mecanico.
- Se necesita cercania sin perder control del flujo operativo.

Objetivo de esta iteracion:

- Ajustar respuestas del agente para que suenen humanas, breves y accionables.

Reglas de estilo:

1. Mensajes cortos (max 3 bloques).
2. Confirmar entendimiento antes de pedir mas datos.
3. Evitar frases de relleno y tono corporativo rigido.

Guardrails de negocio:

1. No prometer resoluciones fuera del sistema.
2. Si la consulta es out-of-scope, responder claro y redirigir.
3. Mantener trazabilidad: area, datos faltantes y siguiente paso.

Criterios de aceptacion:

1. Mejora perceptible de tono sin perder claridad operativa.
2. No aumenta tickets mal clasificados por sobre-humanizar.
3. Manejo out-of-scope consistente.

Salida esperada del asistente:

1. Ajustes de texto/prompt aplicables al flujo actual.
2. Ejemplos antes/despues en casos reales.
3. Recomendaciones para mantener consistencia.

# Resultado observado

Prompt eficaz para humanizar sin romper la logica de negocio.
