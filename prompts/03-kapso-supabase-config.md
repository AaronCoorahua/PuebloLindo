# Prompt 

Actua como Integration Engineer senior.

Necesito un runbook de configuracion de Kapso + Supabase para un backend FastAPI en produccion y local.

Objetivo:

- Asegurar que el flujo WhatsApp -> webhook -> ticket -> respuesta funcione sin configuracion manual difusa.

Incluye de forma obligatoria:

1. Matriz de variables de entorno (nombre, obligatorio, ejemplo, riesgo si falta).
2. Secuencia paso a paso de Kapso:
	- conectar numero
	- obtener API key
	- obtener phone_number_id
	- configurar webhook URL
3. Secuencia paso a paso de Supabase:
	- crear tablas
	- crear indices
	- validar acceso con service role key
4. Plan de pruebas por capas:
	- prueba SQL
	- prueba endpoint local
	- prueba webhook real
5. Troubleshooting de top 10 errores con accion concreta.

Formato de salida:

- Checklist ejecutable.
- Comandos copy-paste (PowerShell + curl).
- Seccion final de "si falla, revisa esto primero".

# Resultado observado

Funciono bien porque bajo la ambiguedad operacional y acelero la integracion real.
