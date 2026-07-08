# agents.md — Instrucciones para la IA: crear el spec.md de una app nueva

Este directorio contiene **plantillas de especificación** para apps de
ingeniería Cox. Si te piden "crear el spec / arrancar una app nueva / hacer la
especificación" y tienes acceso a estas plantillas, **sigue este
procedimiento**. Las plantillas son el punto de partida; el entregable es el
`spec.md` de la app nueva.

## Principio rector

Estas plantillas describen *qué decidir y documentar*, **no** una aplicación
concreta. La app nueva puede tener una arquitectura totalmente distinta a
cualquier proyecto previo. **No arrastres supuestos** (ni de StoreCox ni de
otros): cada decisión se toma para esta app.

## Ficheros de este directorio

| Fichero | Rol |
| --- | --- |
| `README.md` | Visión general del método y el proceso (para humanos) |
| `cuestionario_inicio.md` | Brief de entrada que rellena el usuario (input del Paso 0) |
| `spec_vision.md` | Esqueleto del `spec.md` a rellenar |
| `spec_architecture.md` | Guía de decisión de arquitectura (patrones A–E) |
| `spec_visual_id.md` | Identidad visual Cox (reutilizable casi literal) |
| `spec_conventions.md` | Estándares de entrega [NORMATIVO]: números, idioma del código, documentación |
| `spec_licensing.md` | Esquema de protección, solo si hay distribución externa |
| `agents.md` | Este fichero |

## Convenciones en las plantillas

- `{{marcador}}` → debes sustituirlo por contenido real. **Ningún `{{}}` debe
  sobrevivir** en el spec final.
- **[NORMATIVO]** → contrato corporativo (identidad de marca, formato de
  licencia, contacto de soporte). Consérvalo salvo instrucción explícita en
  contra; si lo cambias, dilo y justifícalo.
- **[ELEGIR]** → punto de decisión: presenta las opciones al usuario o decide
  con criterio y deja constancia de por qué.

## Procedimiento (síguelo en orden)

### Paso 0 — Entender antes de escribir

**Si existe un `cuestionario_inicio.md` relleno, parte de él**: es el brief de
entrada. Léelo entero y úsalo como base. Si no existe, ofrécelo al usuario para
que lo rellene, o condúcelo tú haciéndole esas mismas preguntas.

No empieces a redactar hasta poder responder:

- ¿Qué resuelve la app y para quién? ¿Qué decisiones permite tomar?
- ¿Hay código/prototipos/ejecutables/Excel de planificación que reutilizar?
  Si los hay, **explóralos** (léelos) antes de proponer nada.
- ¿Cómo se usa (escritorio/web/CLI/servicio) y cómo se distribuye?
- ¿Se reparte a terceros como binario? (decide si aplica `spec_licensing.md`).

Si el brief deja huecos esenciales, **pregunta**; no los inventes. Convierte
fechas relativas en absolutas.

### Paso 1 — Visión y alcance

Copia `spec_vision.md` al `spec.md` de la app nueva. Rellena §1 (visión) y §2
(alcance V1 / fuera de alcance). No avances sin esto cerrado.

### Paso 2 — Arquitectura  **[ELEGIR]**

Abre `spec_architecture.md`. Recorre las preguntas previas y el árbol de
decisión. Elige un patrón (A monolítica · B GUI+CLI · C cliente/servicio ·
D web · E librería/CLI), **combínalos o propón otro** si encaja mejor.

- Escribe en §4 del spec: patrón elegido, **por qué**, alternativas
  descartadas, diagrama de bloques, estructura de repo, interfaces,
  persistencia, concurrencia, empaquetado y estrategia de pruebas.
- Si eliges B, usa el anexo §5 (contrato shell↔CLI). Para otros patrones,
  define el contrato equivalente; no copies el de B por inercia.

### Paso 3 — Identidad visual

Aplica `spec_visual_id.md`. Es transversal y casi no cambia entre apps:
paleta Cox, tokens claro/oscuro centralizados, Red Hat Display empaquetada,
gráficas tematizadas, sin colores hardcodeados. Adáptalo al stack elegido
(no asumas PyQt/matplotlib si la app es web u otra cosa).

### Paso 4 — Convenciones de entrega  **[NORMATIVO]**

Incorpora `spec_conventions.md` al spec (en requisitos no funcionales o anexo)
y respétalas al implementar:

- Números decimales a **2 decimales** en UI e informes, con **unidad
  adyacente** (celda/etiqueta contigua); redondeo solo al mostrar, nunca en
  cálculo ni persistencia.
- **Comentarios y docstrings del código en inglés** (aunque la UI esté en
  español); docstring en cada módulo/clase/función pública.
- Entregar **documentación de usuario** (cómo ejecutar y usar) y
  **documentación técnica** (arquitectura y flujo a nivel de desarrollo),
  versionadas y actualizadas con cada versión.
- **Markdown limpio**: redacta el `spec.md` (y todo `.md`) para pasar
  markdownlint sin avisos — líneas en blanco alrededor de encabezados y listas,
  tablas con pipes espaciados, vallas de código siempre con lenguaje (usa `text`
  para diagramas ASCII), sin blancos múltiples ni blancos dentro de blockquotes.
  Detalle y config en `spec_conventions.md` §4 y `markdownlint.jsonc`.

Solo recorta una convención si el usuario lo justifica explícitamente.

### Paso 5 — Protección (condicional)

Si la app se distribuye como ejecutable/binario a terceros, incorpora
`spec_licensing.md` en §7bis y resume las decisiones. Si no, **elimina** esa
sección. Recuerda el contacto de soporte [NORMATIVO] y la advertencia de
custodia de la clave privada.

### Paso 6 — Cerrar el spec

Completa requisitos no funcionales, modelo de datos, roadmap, criterios de
aceptación y riesgos. **Cada criterio de aceptación debe ser verificable**
(traducible a una prueba).

### Paso 7 — Revisar

- No queda ningún `{{marcador}}` sin resolver.
- Se eliminaron las secciones que no aplican.
- Las decisiones [ELEGIR] están justificadas.
- Las convenciones de entrega [NORMATIVO] están reflejadas en el spec.
- Nada presupone una arquitectura o stack que no se haya decidido en el Paso 2.

## Salida esperada

Un único `spec.md` autocontenido para la app nueva, listo para iniciar el
desarrollo, que un tercero pueda leer sin conocer estas plantillas ni proyectos
anteriores.

## Qué NO hacer

- No copies módulos, rutas, nombres de fichero ni decisiones de StoreCox u
  otra app "porque sí". Reutiliza patrones, no implementaciones, salvo que el
  usuario lo pida.
- No dejes el patrón B (GUI+CLI) como elección por defecto: es una opción más.
- No saltes el Paso 0. Un spec sin entender el problema es ruido.
