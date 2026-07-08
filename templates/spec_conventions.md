# Convenciones de entrega  **[NORMATIVO]**

> Estándares transversales que aplican a **toda** app de ingeniería Cox,
> independientemente del dominio, el stack o la arquitectura elegida. Inclúyelos
> en el `spec.md` de la app (sección de requisitos no funcionales o anexo) y
> respétalos en la implementación. Son contrato corporativo: cambiarlos es una
> decisión consciente, no un descuido.

## 1. Formato de números en UI e informes

- Los números con decimales se muestran con **precisión centesimal** (dos
  decimales): `1.23`, `0.50`, `1234.00`.
- **Siempre acompañados de su unidad** en una celda o texto adyacente (no
  dentro del propio número): el valor en una celda/campo y la unidad en la
  celda/etiqueta contigua. Ej.: `| 12.34 | MWh |`, o `Potencia: 12.34  MW`.
- Aplica a tablas, formularios (valores mostrados), gráficas (ejes/etiquetas) e
  informes (Word/Excel/PDF).
- **Excepciones admitidas, si se justifican en el spec**: identificadores y
  contadores enteros (sin decimales); magnitudes que pierden sentido a dos
  decimales (años, nº de ciclos, nº de unidades → enteros); y campos de
  **edición** donde el usuario introduce el valor (ahí se conserva la precisión
  que teclea; el redondeo centesimal es para **mostrar**, no para almacenar ni
  calcular).
- Regla de implementación: redondear **solo en la capa de presentación**; los
  cálculos y la persistencia usan la precisión completa.

Ejemplo de formateo de presentación (pseudocódigo, adáptalo a tu stack):

```python
def fmt(value):            # solo para MOSTRAR
    return f"{value:,.2f}"  # 1234.00 ; la unidad va en celda/etiqueta aparte
```

## 2. Comentarios y docstrings del código: **en inglés**

- Todo el código entregable lleva **comentarios y docstrings en inglés**, con
  independencia de que la UI o la documentación de usuario estén en español.
- Cada módulo, clase y función pública lleva **docstring** que explique
  propósito, parámetros, retorno y errores/efectos relevantes.
- Los nombres de identificadores (funciones, variables, clases) en inglés y
  descriptivos.
- Motivo: portabilidad del código entre equipos/proyectos y consistencia con el
  ecosistema técnico. (La cara visible al usuario final puede ser local; el
  código no.)

## 3. Documentación a entregar (siempre)

Toda app entrega **dos documentos** vivos, además del `spec.md`:

### 3.1 Documentación de usuario (cómo ejecutar y usar)

- Audiencia: usuario final, no necesariamente técnico.
- Idioma: el de la interfaz (normalmente español).
- Contenido mínimo: requisitos e instalación/arranque; guía paso a paso de cada
  función con capturas; formatos de entrada/salida; interpretación de
  resultados e informes; errores frecuentes y cómo resolverlos; contacto de
  soporte y (si aplica) activación de licencia.

### 3.2 Documentación técnica (flujo y detalles de desarrollo)

- Audiencia: desarrolladores/mantenedores.
- Idioma: inglés o español (preferible inglés, alineado con §2).
- Contenido mínimo: arquitectura y diagrama de bloques; flujo de datos
  extremo a extremo; descripción de módulos y sus responsabilidades; contratos
  e interfaces (esquemas JSON/API); modelo de datos y persistencia; cómo
  construir, empaquetar y probar; decisiones de diseño y sus porqués.

Ambas se mantienen actualizadas con cada versión y se versionan junto al código
(p. ej. `docs/usuario/` y `docs/tecnica/`, o un README + `docs/`).

## 4. Estilo Markdown de la documentación  **[NORMATIVO]**

Todos los `.md` (spec, READMEs, documentación) deben pasar **markdownlint** sin
avisos. Reglas prácticas (entre paréntesis, el código de markdownlint que
evitan):

- **Encabezados rodeados de líneas en blanco**: una línea en blanco encima y
  otra debajo de cada `#`/`##`/`###`. No pegar texto, tabla ni lista justo
  debajo de un encabezado (MD022).
- **Listas rodeadas de líneas en blanco**: una línea en blanco antes del primer
  ítem y después del último (MD032).
- **Una sola jerarquía de `#` por documento**: un único `#` de título y no
  saltar niveles (MD001, MD025).
- **Tablas con pipes espaciados**: `| col | col |` y separador `| --- | --- |`
  (con espacios), consistente en toda la tabla (MD060).
- **Bloques de código con lenguaje**: la valla de apertura siempre indica el
  lenguaje (`python`, `json`, `bash`); para diagramas ASCII, árboles o texto
  plano usa `text` (MD040).
- **Blockquotes sin líneas en blanco internas**: no dejar una línea en blanco
  entre dos líneas `>` (si quieres separar, usa párrafos normales) (MD028).
- **Sin líneas en blanco múltiples**: máximo una seguida (MD012).
- **Fichero termina con un único salto de línea final** (MD047).
- **Listas con marcador y sangría consistentes** (p. ej. `-` para viñetas, 2
  espacios de sangría en continuaciones) (MD004, MD007).
- Longitud de línea: envuelve la prosa a ~80–100 columnas por legibilidad; si
  el proyecto no quiere límite estricto, desactiva MD013 en la config (abajo).

**Config recomendada**: copia `markdownlint.jsonc` (en esta carpeta de
plantillas) a la **raíz del proyecto** como `.markdownlint.jsonc`. Fija el
estilo de tablas y relaja MD013 (longitud de línea), manteniendo el resto de
reglas activas. Así el editor marca los avisos de forma consistente para todos.

## Checklist de cumplimiento

- [ ] Números decimales mostrados a 2 decimales, con unidad adyacente.
- [ ] Redondeo solo en presentación; cálculo/persistencia con precisión plena.
- [ ] Comentarios y docstrings del código en inglés; docstring en cada
      módulo/clase/función pública.
- [ ] Documentación de usuario detallada (instalación, uso, resultados, errores).
- [ ] Documentación técnica (arquitectura, flujo, módulos, build, pruebas).
- [ ] Ambas documentaciones versionadas y actualizadas con la versión entregada.
- [ ] Todos los `.md` pasan markdownlint sin avisos; `.markdownlint.jsonc` en la
      raíz del proyecto.
