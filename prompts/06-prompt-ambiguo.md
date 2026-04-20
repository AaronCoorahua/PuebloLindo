# Caso de prompt que no funciono al inicio (anti-pattern sutil)

Necesito una mejora integral del sistema.

Por favor:

1. Fortalece la precision del agente conversacional.
2. Mejora la experiencia del dashboard para operacion diaria.
3. Refuerza estabilidad general sin modificar el comportamiento esperado.
4. Deja la documentacion alineada al estado final del producto.

Consideraciones:

1. Mantener compatibilidad con lo ya implementado.
2. Priorizar cambios de alto impacto con bajo riesgo.
3. Evitar retrabajo innecesario.

# Por que no funciono

1. Suena ordenado, pero no delimita alcance tecnico por modulo o archivo.
2. "Mejora integral" y "alto impacto" no definen un objetivo verificable.
3. "Sin modificar comportamiento esperado" bloquea cambios que eran necesarios para mejorar.
4. No incluye criterios de aceptacion ni casos de prueba para decidir terminado/no terminado.

# Version corregida que si funciono

Iteracion 1 (backend agente):

1. Implementar intake por area con threshold de completitud.
2. Solicitar confirmacion explicita SI/NO antes de crear ticket.
3. Permitir cancelar intake y limpiar sesion.
4. Mantener idempotencia por external_message_id en webhook.

Criterios de aceptacion de iteracion 1:

1. Mensaje ambiguo: no crea ticket, solicita datos faltantes.
2. Mensaje completo + SI: crea ticket.
3. cancel/cancelar: no crea ticket y limpia estado temporal.

Iteracion 2 (frontend):

1. Consolidar /home, /history y /reports con estados de carga/error.
2. Validar cierre de ticket con campos obligatorios.

Iteracion 3 (docs):

1. README con setup local, Kapso, Supabase y flujos de prueba.

# Aprendizaje

Un prompt puede verse profesional y aun asi fallar si no define alcance ejecutable, salida esperada y criterios medibles.