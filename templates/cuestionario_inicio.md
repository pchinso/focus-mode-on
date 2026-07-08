# Cuestionario de inicio de desarrollo —}

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

- **Nombre (provisional)**: {{Focus Mode On}}
- **Frase de una línea** (qué es, para quién): {{getion de tareas personal y mejora de productividad}}
- **Promotor / responsable**: {{pchinso}}
- **Equipo previsto** (iniciales/roles): {{solo usuario pchinso}}

## 2. Problema y objetivo (visión)

- **¿Qué problema resuelve?** {{gestion de tareas como areas de actividad con Iniciativas y proyectos internos }}
- **¿Qué decisiones permite tomar al usuario?** {{Actualizar el trabajo completado y visualizar el pendiente}}
- **¿Qué se hace hoy sin esta app y por qué no basta?** {{se intento con obsidian pero falta una capa de automatizacion en el proceso de marcar a partir de texto de entrada natural la creacion de nuevas tareas y la complitud de la hechas]}}
- **¿Cómo se medirá que ha tenido éxito?** {{mejorar en el dia con el seguientos de actividades de trabajo y personal}}

## 3. Usuarios y contexto de uso

- **¿Quién la usa?** (perfil, nivel técnico): {{yo desarrollador}}
- **¿Cuántos usuarios y a la vez?** {{`1}}
- **¿Dónde la usan?**
  - [ ] Escritorio Windows offline
  - [X] Navegador web
  - [ ] Línea de comandos / scripts
  - [ ] Servidor / servicio
  - [ ] Embebida en otra herramienta
  - [ ] Otro: {{...}}
- **¿Idioma(s) de la interfaz?** {{en}}

## 4. Alcance

- **Imprescindible en la V1** (lo que sí o sí debe estar):
  1. {{Listado de tareas pendientes y completadas}}
  2. {{Capa IA para la actualizacion mediante entradas de texto natural}}
  3. Capacidad de generar  imagenes semanticamente relevantes que sirvan para una identificacion  facil diferentes lineas de proceso de actividades en refereencia a iniciativas y o proyectos.
  4. Todos los archivos son em base archivos Markdown .md legibles y correctamente formateados fuera de la app GUI.
  5. La GUI navegador inperpreta visualmente los archivoa para presentarlos de forma visual atractiva.
- **Deseable más adelante** (roadmap): {{capacidad de ingesta de informacion para la creacion de contextos, busqueda online de informacion relevante}}
- **Explícitamente FUERA de alcance**: {{sin definir}}

## 5. Activos existentes a reutilizar  *(muy importante)*

- **¿Hay código/prototipos/notebooks?** Rutas o repos: {{solo ejemplo de notas diarias Obsidian en "references"}}
- **¿Ejecutables o motores legacy?** ¿En qué lenguaje? {{no}}
- **¿Excel/documentos de planificación o de cálculo de referencia?** {{no}}
- **¿Hay una GUI o diseño previo que sirva de base?** {{no}}
- **¿Qué se debe ignorar/descartar de lo existente?** {{las referencia son solo por contexto no por diseño}}

## 6. Arquitectura y plataforma  *(preferencias y restricciones)*

> La decisión final se toma con `spec_architecture.md`; aquí solo lo que ya
> sepas o exijas.

- **Sistema operativo objetivo**: {{multiplataforma}}
- **Lenguaje/stack preferido o impuesto** (si lo hay): {{Python/web}
- **¿Restricciones de TI?** (sin servidor, sin internet, antivirus, permisos): {{framework ligero y rapido, que permita hospedaje gratuito y gestion sencilla de actualizaciones via github}}
- **Intuición de patrón** (sin compromiso):
  - [ ] App de escritorio monolítica
  - [ ] GUI + motores de cálculo CLI (contrato JSON)
  - [ ] Cliente + servicio/API
  - [X] Aplicación web
  - [ ] Librería / CLI sin GUI
  - [ ] No lo sé — que se proponga

## 7. Datos: entradas y salidas

- **Entradas** (qué datos consume, formatos: JSON/CSV/Excel/BD, volumen): {{.md}}
- **Salidas** (qué produce: tablas, gráficas, informes, ficheros): {{.md}}
- **¿Series temporales o grandes volúmenes?** Resolución y tamaño: {{no}}
- **¿Persistencia?** ¿Hay que guardar proyectos/escenarios/historial? {{puede ser interesante alguna db, tipipo vector db semantica}}
- **¿Librerías de datos de referencia?** (catálogos, fabricantes, tablas): {{puede ser intersante en algun proyecto}}

## 8. Cálculos / funcionalidades clave

- **Cálculos o lógica de negocio principales** (lista): {{no en un principio}}
- **¿Optimización, simulación, análisis estadístico?** {{no necesariamente}}
- **¿Tiempos de cálculo esperados?** (segundos / minutos): {{sub segundo}}
- **¿Algo que NO deba bloquear la interfaz?** {{ui disponible siempre rapido y fluido}}

## 9. Distribución y protección

- **¿Cómo se entrega?**
  - [ ] Ejecutable autónomo (instalable/portátil)
  - [ ] Paquete/librería
  - [X] Acceso web/servicio
  - [ ] Otro: {{...}}
- **¿Se reparte a terceros fuera del equipo?** [ ] Sí [x] No
- **Si sí, ¿se necesita protección/licencia?** (caducidad, vinculación a
  máquina, trazabilidad): {{no}}  → activa `spec_licensing.md`.
- En acceso a UI para ver datos mediante Password.
- La informacion subida protegioda por encriptacion
- **¿Soporte/contacto para usuarios?** {{no}}

## 10. Identidad visual

- **¿Aplica identidad Cox estándar?** [x] Sí (por defecto) [ ] Con excepciones: {{...}}
- **¿Modo claro/oscuro?** [x] Ambos [ ] Solo claro [ ] Indiferente
- **¿Necesidades visuales especiales?** (dashboards, mapas, 3D, impresión): {{Visualmente atractiva interpretacion de lineas de actividad}}

## 11. Requisitos no funcionales

- **Rendimiento / límites**: {{rapida para el usuario}}
- **Seguridad / confidencialidad de datos**: {{encriptacion de datos y proteccion de accesos a app}}
- **Accesibilidad / impresión / exportación**: {{generacion de reporte html con indentidad visual}}
- **Mantenimiento**: ¿quién lo mantendrá y por cuánto tiempo? {{pchiso siempre}}

## 12. Planificación

- **Fecha objetivo de primera versión usable**: {{lo antes posible}}
- **Hitos o fechas clave**: {{no hay}}
- **Esfuerzo estimado / disponible**: {{claude Max}}
- **Dependencias externas** (datos, personas, aprobaciones): {{no}}

## 13. Riesgos, dudas y decisiones abiertas

- **Riesgos que ya ves**: {{que no se encuente una interfaz ui atractiva y que sintetiza conceptualmente bien}}
- **Preguntas que tú mismo tienes sin resolver**: {{como sera la interfaz, lo dejo en mano de la IA}}
- **Decisiones que quieres dejar para más adelante**: {{invitacion a externos para colaborar en un proyecto o hilo de actividades}}

---

## Notas libres

{{Cualquier cosa que no encaje arriba: contexto, ejemplos, capturas, enlaces…}}

---

> **Siguiente paso**: entrega este cuestionario relleno. Con él, sigue el
> procedimiento de `agents.md` para producir el `spec.md` de la app, usando
> `spec_vision.md`, `spec_architecture.md`, `spec_visual_id.md` y
> (si aplica) `spec_licensing.md`.
