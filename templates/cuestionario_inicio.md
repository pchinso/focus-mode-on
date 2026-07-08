# Cuestionario de inicio de desarrollo — {{NOMBRE_PROVISIONAL_APP}}

> **Para qué sirve**: capturar, en un solo sitio, todo lo necesario para
> arrancar la definición de una app nueva. Rellena lo que sepas (deja en blanco
> o marca «por decidir» lo que no); este documento es el **punto de entrada**:
> alimenta el Paso 0 de `agents.md` y, a partir de él, se redacta el `spec.md`.
>
> No hace falta responderlo perfecto ni completo: cuanto más detalles, menos
> preguntas harán falta después. Marca con `[x]` las casillas que apliquen.

Fecha: {{YYYY-MM-DD}} · Autor: {{nombre}} · Versión del brief: {{v1}}

---

## 1. Identidad del proyecto

- **Nombre (provisional)**: {{...}}
- **Frase de una línea** (qué es, para quién): {{...}}
- **Promotor / responsable**: {{...}}
- **Equipo previsto** (iniciales/roles): {{...}}

## 2. Problema y objetivo (visión)

- **¿Qué problema resuelve?** {{...}}
- **¿Qué decisiones permite tomar al usuario?** {{...}}
- **¿Qué se hace hoy sin esta app y por qué no basta?** {{...}}
- **¿Cómo se medirá que ha tenido éxito?** {{...}}

## 3. Usuarios y contexto de uso

- **¿Quién la usa?** (perfil, nivel técnico): {{...}}
- **¿Cuántos usuarios y a la vez?** {{...}}
- **¿Dónde la usan?**
  - [ ] Escritorio Windows offline
  - [ ] Navegador web
  - [ ] Línea de comandos / scripts
  - [ ] Servidor / servicio
  - [ ] Embebida en otra herramienta
  - [ ] Otro: {{...}}
- **¿Idioma(s) de la interfaz?** {{es / en / …}}

## 4. Alcance

- **Imprescindible en la V1** (lo que sí o sí debe estar):
  1. {{...}}
  2. {{...}}
- **Deseable más adelante** (roadmap): {{...}}
- **Explícitamente FUERA de alcance**: {{...}}

## 5. Activos existentes a reutilizar  *(muy importante)*

- **¿Hay código/prototipos/notebooks?** Rutas o repos: {{...}}
- **¿Ejecutables o motores legacy?** ¿En qué lenguaje? {{...}}
- **¿Excel/documentos de planificación o de cálculo de referencia?** {{...}}
- **¿Hay una GUI o diseño previo que sirva de base?** {{...}}
- **¿Qué se debe ignorar/descartar de lo existente?** {{...}}

## 6. Arquitectura y plataforma  *(preferencias y restricciones)*

> La decisión final se toma con `spec_architecture.md`; aquí solo lo que ya
> sepas o exijas.

- **Sistema operativo objetivo**: {{Windows 10/11 · multiplataforma · …}}
- **Lenguaje/stack preferido o impuesto** (si lo hay): {{Python/PyQt · web · …}}
- **¿Restricciones de TI?** (sin servidor, sin internet, antivirus, permisos): {{...}}
- **Intuición de patrón** (sin compromiso):
  - [ ] App de escritorio monolítica
  - [ ] GUI + motores de cálculo CLI (contrato JSON)
  - [ ] Cliente + servicio/API
  - [ ] Aplicación web
  - [ ] Librería / CLI sin GUI
  - [ ] No lo sé — que se proponga

## 7. Datos: entradas y salidas

- **Entradas** (qué datos consume, formatos: JSON/CSV/Excel/BD, volumen): {{...}}
- **Salidas** (qué produce: tablas, gráficas, informes, ficheros): {{...}}
- **¿Series temporales o grandes volúmenes?** Resolución y tamaño: {{...}}
- **¿Persistencia?** ¿Hay que guardar proyectos/escenarios/historial? {{...}}
- **¿Librerías de datos de referencia?** (catálogos, fabricantes, tablas): {{...}}

## 8. Cálculos / funcionalidades clave

- **Cálculos o lógica de negocio principales** (lista): {{...}}
- **¿Optimización, simulación, análisis estadístico?** {{...}}
- **¿Tiempos de cálculo esperados?** (segundos / minutos): {{...}}
- **¿Algo que NO deba bloquear la interfaz?** {{...}}

## 9. Distribución y protección

- **¿Cómo se entrega?**
  - [ ] Ejecutable autónomo (instalable/portátil)
  - [ ] Paquete/librería
  - [ ] Acceso web/servicio
  - [ ] Otro: {{...}}
- **¿Se reparte a terceros fuera del equipo?** [ ] Sí [ ] No
- **Si sí, ¿se necesita protección/licencia?** (caducidad, vinculación a
  máquina, trazabilidad): {{...}}  → activa `spec_licensing.md`.
- **¿Soporte/contacto para usuarios?** {{nombre · email · teléfono}}

## 10. Identidad visual

- **¿Aplica identidad Cox estándar?** [ ] Sí (por defecto) [ ] Con excepciones: {{...}}
- **¿Modo claro/oscuro?** [ ] Ambos [ ] Solo claro [ ] Indiferente
- **¿Necesidades visuales especiales?** (dashboards, mapas, 3D, impresión): {{...}}

## 11. Requisitos no funcionales

- **Rendimiento / límites**: {{...}}
- **Seguridad / confidencialidad de datos**: {{...}}
- **Accesibilidad / impresión / exportación**: {{...}}
- **Mantenimiento**: ¿quién lo mantendrá y por cuánto tiempo? {{...}}

## 12. Planificación

- **Fecha objetivo de primera versión usable**: {{...}}
- **Hitos o fechas clave**: {{...}}
- **Esfuerzo estimado / disponible**: {{...}}
- **Dependencias externas** (datos, personas, aprobaciones): {{...}}

## 13. Riesgos, dudas y decisiones abiertas

- **Riesgos que ya ves**: {{...}}
- **Preguntas que tú mismo tienes sin resolver**: {{...}}
- **Decisiones que quieres dejar para más adelante**: {{...}}

---

## Notas libres

{{Cualquier cosa que no encaje arriba: contexto, ejemplos, capturas, enlaces…}}

---

> **Siguiente paso**: entrega este cuestionario relleno. Con él, sigue el
> procedimiento de `agents.md` para producir el `spec.md` de la app, usando
> `spec_vision.md`, `spec_architecture.md`, `spec_visual_id.md` y
> (si aplica) `spec_licensing.md`.
