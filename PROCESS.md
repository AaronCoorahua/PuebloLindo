## 2.3 Reflexion del proceso

### 1) En que momento cambie de enfoque y por que

Al inicio el objetivo era solamente clasificar mensajes y probar la logica en local.
Ese enfoque cambio cuando vi que integrar el webhook de Kapso en local implicaba manejar ngrok y tunnels de forma continua, lo cual agregaba friccion para un MVP.

Por eso migre el enfoque a despliegue en nube con Vercel para tener una URL estable y acelerar pruebas reales de extremo a extremo.

Ademas, durante las iteraciones hice dos cambios de enfoque funcionales:

- Primero, el agente respondia de forma muy robotica, asi que ajuste prompts y respuestas para que suene mas humano en WhatsApp.
- Luego, pase a un modelo con areas definidas y alcances claros por area, para mejorar la deteccion y evitar ambiguedades.
- Finalmente, agregue umbral de completitud y confirmacion explicita para no crear tickets con informacion insuficiente.

### 2) Como use IA y que prompts funcionaron o fallaron

Use la IA como asistente de codigo para construir el MVP rapido.
Principalmente me ayudo en tres frentes:

- Acelerar implementacion backend y frontend sin partir de cero en cada modulo.
- Generar mockups y estructura de interfaz para visualizar el Kanban y sus estados.
- Leer y aterrizar documentacion de Kapso y Supabase para configurarlos correctamente en el proyecto.

Prompts que funcionaron mejor:

1. Definir arquitectura MVP full-stack y flujo de tickets de WhatsApp a dashboard.
2. Pedir mockups/estructura de Kanban para tener una base visual rapida.
3. Endurecer el agente con areas, alcance, umbral y confirmacion antes de crear ticket.

Prompts que fallaron o funcionaron regular:

1. Prompts con alcance combinado (backend + frontend + docs en una sola iteracion) generaban avances, pero dispersos.
2. Prompts sin criterios de aceptacion medibles hacian dificil validar si una iteracion estaba realmente terminada.
3. Pedidos de tono conversacional sin ejemplos de entrada/salida quedaban demasiado generales y requerian refinamiento.
4. Restricciones contradictorias ("mejora todo" pero "sin cambios estructurales") redujeron calidad de la primera respuesta.

Prompts usados durante iteraciones en esta carpeta:

- [prompts/01-mvp-rapido.md](prompts/01-mvp-rapido.md)
- [prompts/02-mockup-kanban.md](prompts/02-mockup-kanban.md)
- [prompts/03-kapso-supabase-config.md](prompts/03-kapso-supabase-config.md)
- [prompts/04-agente-mas-humano.md](prompts/04-agente-mas-humano.md)
- [prompts/05-areas-umbral-confirmacion.md](prompts/05-areas-umbral-confirmacion.md)
- [prompts/06-prompt-ambiguo.md](prompts/06-prompt-ambiguo.md)

### 3) Que mejoraria si tuviera una semana mas

Si tuviera una semana adicional, priorizaria:

1. Mejorar la autenticacion de la aplicacion para endurecer acceso y sesiones.
2. Implementar handoffs y notificaciones cuando se crea un ticket:
	- Correo automatico por area responsable.
	- Mensaje de WhatsApp a numeros encargados por area.
	- Si el agente no puede asignar con certeza a un area operativa, crear el ticket en "otros" para revision humana y reasignacion posterior.
3. Profundizar en el analisis de areas especificas del marketplace para mejorar el prompt del agente, reducir falsos positivos y elevar precision de clasificacion.
4. Mejorar el flujo del agente. Afinar edge cases, medir casos de uso, y lograr que el agente actue de la mejor forma ante cualquier escenario posible en Producción.

### 4) Puntos adicionales (opcional)

1. Deteccion de incertidumbre y escalamiento a humano:
	- El flujo evita decisiones forzadas cuando no hay evidencia suficiente.
	- Si no se puede resolver con certeza por area, el ticket se enruta a "otros" y queda listo para handoff humano.

2. Control de alucinacion y verificacion de informacion:
	- Se uso tipado estricto (schemas) y tools deterministas para limitar decisiones a datos disponibles.
	- La logica de negocio exige campos minimos por area y confirmacion explicita antes de crear ticket.
	- Verificacion aplicada: pruebas manuales por pasos (mensaje ambiguo -> pide faltantes; mensaje completo + SI -> crea ticket) para validar que el sistema no inventa datos no provistos.

3. Escalabilidad propuesta para crecimiento 10x:
	- Incorporar colas con AWS SQS para desacoplar recepcion de webhooks, procesamiento de agente y notificaciones.
	- Mantener frontend y backend en Vercel o Amplify (modelo serverless tipo lambdas) para escalar horizontalmente por demanda.
	- En backend, desacoplar la llamada al LLM del request principal (procesamiento async/worker) y fortalecer concurrencia con asyncio para mejorar throughput y resiliencia.

