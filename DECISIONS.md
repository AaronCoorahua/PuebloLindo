# DECISIONS.md

## 1. Problema elegido y por qué es el más urgente

Elegí abordar el problema de **categorización de tickets en Customer Success**.

Este problema es el más urgente porque impacta directamente en la **experiencia del usuario en momentos críticos**, cuando el cliente ya tiene un problema (pagos, envíos, productos defectuosos, etc.). En estos casos, lo más importante no es solo la resolución final, sino la **rapidez con la que el usuario percibe que su problema está siendo atendido**.

Actualmente, el equipo pierde aproximadamente 4 horas al día clasificando tickets manualmente, lo que retrasa:
- la asignación al equipo correcto,
- la priorización de casos urgentes,
- y la primera respuesta al cliente.

Automatizar la categorización permite:
- reducir el tiempo de enrutamiento a segundos,
- priorizar correctamente los casos críticos,
- enviar una respuesta inmediata indicando que el caso está siendo procesado,
- mejorar la percepción de control y confianza del usuario.

Adicionalmente, **modelar correctamente la entrada de tickets (estructura, idioma, intención)** permite generar datos más limpios y consistentes, lo cual es clave para una futura automatización del volumen de mensajes (problema A), ya que facilita identificar patrones, FAQs y casos repetitivos.

En resumen, la categorización es el punto de mayor impacto inmediato porque:
- reduce carga operativa,
- mejora tiempos de respuesta (SLA),
- y crea una base sólida para escalar automatización en el futuro.

---

## 2. Herramientas y arquitectura elegidas

La solución se diseña como un **sistema de triage automatizado asistido por IA**, donde el modelo interpreta el lenguaje natural y una capa de reglas garantiza control operativo.

### Stack tecnológico

- **Frontend: Next.js**
  - Interfaz simple para visualizar tickets y resultados.
  - Permite escalar a dashboard operativo en el futuro.

- **Backend: FastAPI (Python)**
  - API para procesar tickets.
  - Rápido de implementar y adecuado para pipelines de IA.

- **Base de datos: Supabase**
  - Persistencia de tickets, resultados y logs.
  - Fácil integración y despliegue rápido.

- **Despliegue: Vercel**
  - Hosting del frontend.
  - Integración sencilla para MVP.

- **Mockups: Banani**
  - Prototipado rápido de flujos y UI antes de implementar.

- **Herramienta de desarrollo: Copilot (GPT-5.3 Codex)**
  - Asistencia en generación de código y aceleración del desarrollo.

---

### Modelo de IA

- **Modelo principal: Gemini Flash**
  - Elegido por su:
    - alta velocidad,
    - bajo costo,
    - buen rendimiento en clasificación multilingüe.

- **Fallback: Gemini 3 Flash Preview**
  - Se utiliza en caso de:
    - saturación del modelo principal,
    - errores de disponibilidad.

---

### Arquitectura (alto nivel)

```text
Input (ticket simulado: WhatsApp / Email)
        ↓
Normalización de entrada
        ↓
LLM (clasificación estructurada)
        ↓
Validación (schema)
        ↓
Reglas de negocio
        ↓
Decisión:
   ├── Respuesta automática (casos simples)
   └── Escalamiento a humano (casos complejos)
        ↓
Asignación a equipo
        ↓
Persistencia en Supabase