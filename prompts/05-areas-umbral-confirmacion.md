# Prompt de intake por umbral 

Rol: Actua como Backend Engineer enfocado en calidad de tickets.

Contexto:

- El sistema estaba creando tickets muy temprano con mensajes vagos.
- Necesitamos gatear creacion por calidad minima de contexto.

Objetivo de esta iteracion:

- Implementar un flujo de intake multi-turno antes de crear ticket.

Requerimientos funcionales:

1. Definir campos required y mandatory por area.
2. Calcular completitud y comparar con threshold por area.
3. Si no cumple, pedir datos faltantes.
4. Si cumple, solicitar confirmacion explicita SI/NO.
5. Crear ticket solo tras confirmacion afirmativa.
6. Permitir cancelar intake y limpiar sesion.

Requerimientos tecnicos:

1. Sesion temporal por telefono con TTL.
2. Evitar mezcla de slots al cambiar area detectada.
3. Mantener rutas y contratos existentes (sin romper webhook).

Criterios de aceptacion:

1. Mensaje inicial ambiguo no crea ticket.
2. Mensaje completo + SI crea ticket.
3. Cancelar corta flujo y no persiste ticket.

Salida esperada del asistente:

1. Cambios en service.py con funciones auxiliares claras.
2. Ajuste del run_ticket_agent para gatear create/update.
3. Pruebas manuales de STEP1/STEP2/confirmacion.

# Resultado observado

Fue el prompt mas impactante: subio calidad de ticket y redujo ruido operativo.
