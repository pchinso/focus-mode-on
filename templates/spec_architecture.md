# Guía de arquitectura — cómo elegir y documentar

> Plantilla de decisión. No impone una arquitectura: te ayuda a escoger la
> adecuada para **tu** app y a documentarla en §4 de su `spec.md`. Una app
> nueva puede adoptar un patrón completamente distinto al de cualquier proyecto
> anterior; eso es esperado.

## 1. Preguntas previas (responde antes de elegir)

- **¿Quién la usa y dónde?** Escritorio offline · navegador · servidor ·
  línea de comandos · embebida en otra herramienta.
- **¿Dónde está el valor / la complejidad?** Cálculo intensivo · visualización
  · integración de datos · automatización · colaboración multiusuario.
- **¿Hay código existente que reutilizar?** Scripts, notebooks, librerías,
  ejecutables legacy.
- **¿Cómo se distribuye?** Instalable, binario, paquete, servicio, acceso web.
- **¿Cuántos la mantendrán y por cuánto tiempo?** Condiciona modularidad y
  pruebas.

## 2. Patrones de arquitectura  **[ELEGIR]**

Catálogo de opciones habituales. Elige una, combínalas o propón otra; lo que
importa es justificar la decisión.

### A. GUI monolítica

Toda la lógica dentro de la aplicación de escritorio.

- **A favor**: simple, sin orquestación, despliegue único.
- **En contra**: cálculo y UI acoplados; difícil de testear y de reutilizar la
  lógica fuera de la GUI.
- **Cuándo**: utilidades pequeñas, prototipos, lógica ligera.

### B. GUI + motores CLI por contrato (shell ↔ engines)

La GUI orquesta ejecutables/CLIs independientes que intercambian JSON.

- **A favor**: motores testeables y versionables aparte; añadir herramienta sin
  tocar la GUI; reutiliza ejecutables legacy.
- **En contra**: overhead de orquestación (subprocesos, serialización); más
  piezas que empaquetar.
- **Cuándo**: varios motores de cálculo, código legacy a envolver, equipos que
  evolucionan motores y UI por separado.
- **Detalle de contrato**: ver §5 (es el patrón mejor documentado aquí porque
  es el menos obvio de montar bien).

### C. Cliente + servicio/API

UI ligera contra un backend (local o remoto) que expone una API.

- **A favor**: multiusuario, lógica centralizada, clientes diversos
  (web/escritorio).
- **En contra**: requiere infraestructura, despliegue y disponibilidad de red.
- **Cuándo**: colaboración, datos compartidos, acceso desde varios sitios.

### D. Aplicación web

Todo en el navegador (o SSR + backend).

- **A favor**: cero instalación, acceso universal, actualización central.
- **En contra**: stack distinto, seguridad/host, trabajo offline limitado.
- **Cuándo**: alcance amplio de usuarios, sin requisitos de escritorio nativo.

### E. Librería / CLI sin GUI

Solo motor, consumido por scripts u otras apps.

- **A favor**: máxima reutilización y automatización; lo más fácil de testear.
- **En contra**: sin interfaz para usuario final.
- **Cuándo**: el valor es el cálculo y los usuarios son técnicos o son otras
  apps (incluido el patrón B como cliente).

## 3. Árbol de decisión rápido

```text
¿Usuarios no técnicos necesitan interfaz?
├─ No  → E (librería/CLI)
└─ Sí
   ├─ ¿Multiusuario / datos compartidos / acceso remoto? → C o D
   └─ Escritorio
      ├─ ¿Lógica ligera y autocontenida?                   → A
      └─ ¿Varios motores / legacy / cálculo pesado?        → B
```

## 4. Qué documentar en el `spec.md` (sea cual sea el patrón)

1. **Patrón elegido y por qué** (1 párrafo + el criterio que te llevó ahí).
   Menciona alternativas descartadas.
2. **Diagrama de bloques** (ASCII basta): componentes y flujos de datos.
3. **Estructura de repositorio** propuesta y responsabilidad de cada módulo.
4. **Límites e interfaces**: cómo hablan los componentes (llamadas, JSON, API,
   eventos), formatos y esquemas.
5. **Estado y persistencia**: dónde viven datos, configuración y resultados;
   formato; versionado.
6. **Concurrencia / rendimiento**: qué no debe bloquear, qué es asíncrono,
   tiempos esperados.
7. **Empaquetado y despliegue**: cómo se construye y se entrega.
8. **Estrategia de pruebas**: unitarias, integración, end-to-end.

## 5. Anexo: contrato del patrón B (shell ↔ motores CLI)

Solo si eliges B. Es el patrón con más detalle porque montarlo de forma
intercambiable requiere un contrato explícito.

**Contrato motor ↔ GUI** (normativo si adoptas el patrón):

1. Invocación: `motor --input <in.json> --output <out.json> [opciones]`.
2. Exit codes estables: `0` éxito · `1` entrada inválida · `2` cálculo ·
   `3` E/S.
3. Entrada: un único JSON validado (Pydantic recomendado) con su
   `input_schema.json` publicado.
4. Salida: JSON con bloque `meta` (`tool, version, run_timestamp,
   duration_seconds, status, warnings[]`) + resultados; `output_schema.json`
   publicado.
5. Headless: logging a stderr/fichero, sin interacción.

**Manifest declarativo por herramienta** (la GUI no conoce la lógica, solo el
contrato): id, ejecutable, schema, secciones/campos del formulario y mapeo de
resultados a tablas/gráficas. Añadir herramienta = añadir manifest + binario.

**Núcleo típico**: registro de manifests · mapeo formulario↔JSON · validación
contra schema · runner en hilo/subproceso (exit codes, timeout, cancelación) ·
extracción de resultados · persistencia de ejecuciones.

**Pruebas clave**: roundtrip formulario↔JSON · validación con errores mapeados
a campo · end-to-end GUI→motor real→vistas · selftest del empaquetado. Para
testear GUI sin pantalla: `QT_QPA_PLATFORM=offscreen` (Qt).

> Estos detalles existen como referencia; no son obligatorios salvo que elijas
> B. Para A/C/D/E, define el contrato equivalente de tu patrón en §4.4.
