# Prompt de dashboard operativo 

Rol: Actua como Frontend Engineer senior con foco en operacion de soporte.

Contexto:

- Los tickets ya vienen del backend con area, estado, resumen, timestamps y wa_link.
- Se necesita una UI operativa, no solo una maqueta visual.

Objetivo de esta iteracion:

1. Implementar /home en formato Kanban por area.
2. Implementar /history para tickets cerrados.
3. Implementar /reports con contadores y agregados por area.

Requerimientos funcionales:

1. Home: columnas por area con tarjetas accionables.
2. Cierre: formulario con atendedor y mensaje_cierre.
3. History: listado consultable con enlace a WhatsApp.
4. Reports: total open, total closed y conteo por area.

Requerimientos UX:

1. Estados de loading, error y empty en cada vista.
2. Responsive real (mobile y desktop).
3. Boton de recarga en vistas operativas.

Criterios de aceptacion:

1. Se puede cerrar un ticket completo desde home.
2. Al cerrar, history refleja el cambio.
3. Reports muestra datos consistentes con tickets.

Salida esperada del asistente:

1. Plan de componentes y rutas.
2. Implementacion incremental por pagina.
3. Validacion final de flujo de negocio.

# Resultado observado

Prompt efectivo para pasar de layout a flujo real de operacion.
