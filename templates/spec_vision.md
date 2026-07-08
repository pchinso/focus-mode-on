# {{NOMBRE_APP}} — Especificación de Producto y Arquitectura (v{{VERSION}})

> Plantilla de documento de visión/alcance. Copia a `spec.md` del proyecto
> nuevo, rellena los `{{marcadores}}` y borra esta cita.

**{{NOMBRE_APP}}**: {{frase única que describe qué resuelve la herramienta y para quién}}.

| Campo | Valor |
| --- | --- |
| Documento | spec.md — {{primera versión integrable / revisión}} |
| Fecha | {{YYYY-MM-DD}} |
| Ubicación | `{{C:\_SVN\trunk\NombreApp}}` |
| Estado | {{Borrador / En desarrollo / Beta}} |
| Fuentes | {{repos, prototipos, Excel de planificación, identidad visual}} |

---

## 1. Visión y objetivo

{{Qué es la aplicación, a qué equipo sirve, qué decisiones permite tomar.}}
Lista de capacidades principales (3–6 viñetas, orientadas a resultado, no a
implementación):

- {{Capacidad 1}}
- {{Capacidad 2}}

### 1.1 Principio arquitectónico rector

> {{La decisión de arquitectura de una frase que gobierna todo el diseño.}}

Elige el patrón con `spec_architecture.md` y resúmelo aquí, justificando por
qué encaja con este proyecto (y qué alternativas descartaste).

```text
{{Diagrama ASCII de bloques: componentes y flujos de datos}}
```

---

## 2. Alcance de la V1 (primera versión integrable)

### 2.1 Incluido en V1

| # | Capacidad | Origen |
| --- | --- | --- |
| V1-1 | {{...}} | {{prototipo / motor legacy / nuevo}} |

### 2.2 Excluido de V1 (→ roadmap §9)

- {{Lo que NO entra y por qué; fuera de alcance explícito.}}

---

## 3. Identidad visual

Cumplimiento del manual Cox — ver `templates/spec_visual_id.md`.
{{Resumen de aplicación específica: pantallas con gradiente, paleta de
gráficas, modo claro/oscuro, etc.}}

---

## 4. Arquitectura de la aplicación

{{Patrón elegido (de spec_architecture.md) y su justificación, diagrama de
bloques, estructura de repositorio y responsabilidad de cada módulo, interfaces
entre componentes, persistencia, concurrencia y empaquetado.}}

---

## 5. Componentes / módulos de cálculo

Por cada módulo o motor relevante: **función**, **lógica/modelos que
implementa**, **entrada**, **salida**, **dependencias** y **trabajo de
integración** pendiente.

### 5.1 {{Componente 1}}

{{...}}

---

## 6. Especificación funcional de la GUI (V1)

{{Ventana de bienvenida, ventana principal, panel de herramienta, pestaña
proyectos, visualizaciones mínimas por herramienta, ayuda/about.}}

---

## 7. Requisitos no funcionales

| Tema | Requisito |
| --- | --- |
| Plataforma | {{Windows 10/11 x64; ejecutable PyInstaller autónomo}} |
| Stack | {{Python 3.11+, PyQt6, matplotlib, pandas, pydantic, ...}} |
| Rendimiento | {{La GUI nunca se bloquea; tiempos esperados por motor}} |
| Robustez | {{Validación previa, errores accionables, timeouts}} |
| Trazabilidad | {{Cada run guarda input/output/log/versión/timestamp}} |
| Calidad | {{pytest, tests E2E contra motores reales, selftest del exe}} |
| Idioma | {{UI en español; preparada para i18n}} |
| Identidad | Cumplimiento del manual de identidad Cox (ver spec_visual_id.md) |
| Convenciones de entrega | **[NORMATIVO]** Formato de números (2 decimales + unidad adyacente), código comentado/docstrings en inglés, documentación de usuario y técnica. Ver spec_conventions.md |
| Licenciamiento | {{Ver §7bis si hay distribución externa}} |

### 7bis. Licenciamiento y protección

Si la app se distribuye como ejecutable/binario a terceros, aplica el esquema
de `spec_licensing.md` y resume aquí las decisiones. Si no aplica, borra esta
sección.

---

## 8. Modelo de datos

{{Tablas SQLite / ficheros, convención de unidades, formatos de fecha.}}

---

## 9. Roadmap

| Versión | Contenido | Fases del plan |
| --- | --- | --- |
| **V1.0** | {{...}} | {{...}} |
| **V2.0** | {{...}} | {{...}} |

---

## 10. Criterios de aceptación V1

Lista numerada de comportamientos **verificables** de extremo a extremo
(cada uno debería corresponder a un test). Ej.:

1. Desde el ejecutable, el usuario {{crea caso, ejecuta, obtiene resultados X}}
   sin que la GUI se bloquee y con posibilidad de cancelar.

---

## 11. Riesgos y decisiones abiertas

| Riesgo / decisión | Mitigación / propuesta |
| --- | --- |
| {{...}} | {{...}} |

---

*Documento generado a partir de {{fuentes}}. Plantilla: `spec_vision.md`.*
