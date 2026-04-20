# DECISIONS.md

## 1. Problema elegido y por qué es el más urgente

Elegí el problema de **categorización de tickets en Customer Success**.

Es el más urgente porque impacta directamente en:
- el tiempo de respuesta inicial,
- la correcta asignación de casos,
- y la percepción del usuario en situaciones críticas (pagos, envíos, reclamos).

Actualmente, el equipo pierde ~4 horas/día clasificando manualmente tickets, lo que retrasa:
- el enrutamiento al equipo correcto,
- la priorización de casos urgentes,
- y la primera respuesta al cliente.

Automatizar este paso permite:
- reducir el tiempo de clasificación a segundos,
- enviar una respuesta inmediata ("tu caso fue asignado a X área con un tiempo estimado de atención"),
- mejorar SLA y experiencia del usuario.

Además, **modelar la entrada de tickets (estructura, categorías, idioma, prioridad)** permite generar datos más limpios y consistentes, lo cual habilita en el futuro:
- automatización parcial de respuestas (problema A),
- detección de FAQs,
- análisis de volumen y patrones.

Este enfoque prioriza impacto inmediato y habilita escalabilidad posterior.

---

## 2. Herramientas y arquitectura

### Stack elegido

- **Frontend: Next.js**
  - UI simple para testear tickets y visualizar resultados.
  - Rápido de implementar y fácil de desplegar.
  - Componentes UI con **shadcn/ui** para mantener consistencia visual y acelerar desarrollo.

- **Backend: FastAPI (Python)**
  - Manejo de endpoints (`/triage`).
  - Integración con LLM.
  - Validación de datos.
  - OpenAPI como contrato único del API REST.

- **Base de datos: Supabase**
  - Almacenamiento de tickets procesados.
  - Logs y trazabilidad.

- **Deploy: Vercel**
  - Despliegue rápido del frontend.
  - Integración simple con APIs.

- **Mockups: Banani**
  - Prototipado rápido de interfaz.

- **Coding assistant: GitHub Copilot (GPT-5.3-Codex)**
  - Aceleración de desarrollo.
  - Generación de boilerplate y tests.

- **Canal de entrada (MVP): Kapso (WhatsApp)**
  - Permite simular flujo real de tickets desde WhatsApp.
  - Free tier con 1 número y volumen limitado de mensajes.

### LLM principal

- **Gemini Flash**
  - Alta velocidad.
  - Bajo costo.
  - Suficiente precisión para clasificación estructurada.

Se usa para:
- detección de idioma,
- categorización,
- prioridad,
- y generación de respuesta sugerida.

### Fallback

- **Gemini 3 Flash Preview**
  - Se utiliza si el modelo principal falla o alcanza límites.

### Arquitectura (alto nivel)

```text
Input (WhatsApp vía Kapso / ticket simulado)
        ↓
FastAPI endpoint (/triage)
        ↓
LLM (Gemini Flash -> structured output)
        ↓
Validación (Pydantic)
        ↓
Reglas de negocio
        ↓
Decisión:
   ├── Auto-response (casos simples)
   └── Escalamiento a humano
        ↓
Asignación de equipo
        ↓
Persistencia (Supabase)
        ↓
Respuesta al cliente
```

### ¿Por qué esta combinación?

Se eligió esta arquitectura por:

- **Separación de responsabilidades**
  - El LLM interpreta lenguaje natural.
  - El backend aplica lógica, validación y control.

- **Velocidad de desarrollo (MVP-first)**
  - FastAPI y Next.js permiten iterar rápidamente.
  - Vercel simplifica el despliegue.

- **Bajo costo operativo**
  - Gemini Flash ofrece buen balance entre costo y latencia.
  - Supabase reduce complejidad de infraestructura.
  - Kapso permite integrar WhatsApp rápidamente sin overhead inicial.

- **Escalabilidad futura**
  - La arquitectura desacoplada permite:
    - cambiar el modelo LLM fácilmente,
    - añadir procesamiento asíncrono,
    - integrar nuevos canales (WhatsApp, email).

- **Control sobre la IA**
  - Uso de salidas estructuradas.
  - Validación estricta con schemas.
  - Reglas de negocio para decisiones críticas.

### Contrato API (OpenAPI)

- OpenAPI será la única fuente de verdad del contrato backend-frontend.
- El backend expone el contrato en `/openapi.json` y la documentación en `/docs`.
- Flujo MVP: se cambia backend, se regenera el cliente TypeScript y luego se ajusta el frontend.

### Alineación Frontend-Backend

- Backend: monolito modular por dominio con separación de `router`, `schemas` y `service`.
- Frontend: carpeta `/features` por módulo de dominio.
- Cada feature tendrá `api.ts` y `hooks.ts`; `types.ts` solo cuando sean tipos de UI y no del contrato API.

### Principio de diseño

El sistema sigue un enfoque de **IA asistida, no autónoma**:

- la IA interpreta y estructura información,
- el sistema controla las decisiones operativas.

Esto reduce riesgo y permite escalar con mayor confiabilidad.

### Decisiones clave

- La IA no toma decisiones críticas sola.
- Se usa para interpretación, no para control total.
- Se combinan:
  - LLM (flexibilidad),
  - reglas (control).

---

## 3. Costos aproximados del MVP

### Supuestos

- 1M tokens procesados/mes.
- Uso principalmente de texto.

### Costos

| Concepto | Free Tier | Paid Tier |
|---|---|---|
| Input tokens | Gratis | $0.25 / 1M tokens |
| Output tokens | Gratis | $1.50 / 1M tokens |
| Context caching | N/A | $0.025 / 1M tokens |
| Storage (cache) | N/A | $1.00 / 1M tokens / hora |

### Estimación mensual MVP

- Input: $0.25
- Output: $1.50
- Total estimado: ~$2 - $5 / mes

---

## 4. Limitaciones y alcance

### Limitaciones

- Integración limitada con canales:
  - WhatsApp vía Kapso (free tier: 1 número, volumen limitado).
- Sin integración completa con Gmail.
- No hay contexto histórico del usuario.
- La clasificación depende del prompt (puede fallar en casos ambiguos).
- Categorías limitadas (set fijo).
- Confianza del modelo no calibrada con datos reales.

### Fuera de alcance

- Integración completa con APIs de WhatsApp Business o Gmail.
- Automatización completa de respuestas (chatbot full).
- Fine-tuning de modelos.
- Dashboard analítico.
- Sistema de feedback humano.
- Manejo de archivos/imágenes.

### Siguiente paso (no incluido en MVP)

- Escalar integración con:
  - WhatsApp Api como Tech Provider (mayor volumen y múltiples números),
  - Gmail.
- Evaluar herramientas como:
  - Resend (automatización de emails).
- Agregar interacciones de Human in the loop.
- Evaluar automatizar resolución de tickets.

---

## 5. Riesgos

- Clasificación incorrecta en tickets ambiguos.
- Mensajes con múltiples intenciones.
- Idiomas mezclados.
- Sobreconfianza del modelo.

### Mitigación

- Validación estricta (schema).
- Reglas de negocio.
- Fallback a categoría "Otros" en tickets.

---

## Conclusión

La solución prioriza impacto operativo inmediato:

- automatiza clasificación,
- mejora tiempos de respuesta,
- estructura datos para futuras automatizaciones,

sin perder control en casos críticos.