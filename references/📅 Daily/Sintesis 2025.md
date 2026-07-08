---
tags:
  - sintesis
  - daily
  - "2025"
  - revision-claude
fuente: "📅 Daily/2025 (238 notas)"
generado: 2026-06-10
---

# Síntesis Daily 2025

Cronología de hitos y decisiones extraída de las 238 notas diarias de 2025. Solo se recoge el contenido duradero; las conversaciones con IA pegadas en bruto se han condensado (el detalle técnico útil está en [[Referencia rescatada 2025-2026]]).

## Cronología por meses

### Enero
- **Propósito del año** (02/01): entrada en la década de los 40. Objetivo principal 2025: bajar del ~25% de grasa corporal a **<15% en verano**, manteniendo masa muscular (borradores de post para Reddit r/hybridathletes).
- Consultas técnicas guardadas: OpenUSD + datos geoespaciales en Python, script robocopy de sincronización del vault, procedimiento de **flash test de módulos FV según IEC 60904-2 / 61215** (21–28/01).
- Nota suelta (30/01): "2025_Obsidian vault / ThisSummer12fat" (apunte críptico, posible clave o lema del objetivo anual).

### Febrero
- Trabajo activo en: [[PV Solar projects software]], [[BESS offers]], [[Django MTS]], [[Khi Optical Performance]], [[BESS Tool internal DMC]].
- **Citas DNI** concertadas (20/02) para el 03/03 y 04/03 en Dos Hermanas.
- Incidencia licencia **AICON 3D Studio** (dongle no reconocido en PC nuevo, v11.01.02) — gestión con Hexagon (27/02).
- Fix del error de encoding en `read_panond` (pvlib) para el conversor PVsyst PAN/OND → CS (24/02).

### Marzo
- **Preparación del viaje a Sudáfrica (Khi Solar One)**: [[Khi Travel Plan]], [[Khi Field Measurements]], [[Aicon Equipments]]. Justificación en aduana: formación de personal local en procedimientos de medida (18/03).
- Cálculo de duración del viaje: **24 de marzo – 17 de abril (25 días)** (21/03).
- Inicio del curso Coursera "Data Analytics Foundations" (18/03).

### Abril — Misión en Khi Solar One (Sudáfrica) 🏆
- **Hito laboral del año**: 3 semanas en la planta CSP Khi Solar One (4.120 heliostatos, Upington/Northern Cape) formando al personal local en fotogrametría y ajuste de canteo de heliostatos.
  - 02/04: log de la primera semana — 5 revisiones completas, personal local ganando autonomía.
  - 14/04: email de cierre — **+20 medidas de fotogrametría supervisadas**, formación completada, equipo de fotogrametría entregado en planta (detalle en Referencia).
  - Estancia en guesthouse: 27/03 – 16/04 (20 noches; 1ª noche pagada también en Protea Hotel).
- 29/04: **análisis del histórico de calibraciones de heliostatos** (266.685 registros 2023–2025): solo 32,67% de calibraciones exitosas; intervalo medio 36 días; 81% de los fallos en 3 causas. Informe enviado a planta.
- Vida personal: respuesta formal a la administración de fincas (Isabel) contra la **prohibición de juego infantil en zonas comunes** (Art. 39 CE, LO 1/1996, Ley de Propiedad Horizontal) (08/04).
- Perfil deportivo anotado (12/04): 40 años, ingeniero, corriendo desde los 17, ex-duatleta/triatleta sub-23, padre de gemelos hace 7 años, 78 kg / 176 cm (venía de 84 kg), plantillas por pronación/pie valgo, Z2 a 6:00 min/km hasta 20 km.

### Mayo — Herramienta de Albedo (Google Earth Engine)
- Desarrollo de la **herramienta de análisis de albedo** con GEE + MODIS MCD43A3 (repo GitHub `pchinso/Albedo_earth_engine`). Primeros análisis: BELA BELA (Sudáfrica).
- 26/05: petición de Víctor Figueroa (Sizing & Performance) para la **oferta PVSP BW7 Infinity Ngwedi (Sudáfrica, plantas OS1/OS2)** — albedo cliente 0,2 vs 0,13–0,15 obtenido. Inicio de una serie de informes de albedo por proyecto que dura todo el año.
- Exploración de cobertura de nubes por satélite (GOES, Meteosat/EUMETSAT, Cloud Score+ Sentinel-2) para zona de Dubái — soporte al trabajo DEWA.
- 29/05: **candidatura de empleo externa** — Técnico de Electromedicina en Getinge (Sevilla); reutiliza carta de 2024 para Technical PM. Señal de búsqueda activa de empleo fuera de Cox.

### Junio
- Cadena de informes de albedo: **El Sanate (Guatemala)**, **Corbii (Rumanía)**, **Piñon (Madrid)**, **Peñaflor (Zaragoza)**, **Nimbo (Madrid)** — siempre comparativa 5 km vs 0,5 km de radio.
- Proyecto **_Auto PTX Reports** (animaciones T5 con matplotlib): solicitud a IT de permisos para instalar ffmpeg y modificar PATH (03/06).
- Utilidades Python varias (extraer ZIPs, borrar carpetas vacías, filtrar CSV) para el procesado de datos de planta.

### Julio — Modelo híbrido PV+BESS
- **Modelo horario de planta híbrida PV+BESS en Python** (proyecto H2 Hysencia): PV 59,99 MWp + BESS 175 MWh / 35 MW, producción mínima garantizada 18 MW AC. Iteraciones con BESS de 75 a 250 MWh (tabla de sensibilidad en Referencia). Carpeta: `25_Work_2025/BESS/HybridModel`.
- Proyecto **DEWA Historical Data con Polars** (`2501_Dewa_Historical_data_Polars`): procesado de Excel históricos, múltiples fixes (headers, datetime, xlsb).
- Más albedo: **Quiquima (España)**, **Doral (Marruecos)**, **Onderstepoort Infinity Cluster (SA)** a 0,5 km (respuesta a Víctor Figueroa, 10/07).
- 30/07: "Reunión IDbs".

### Agosto
- Sin contenido (solo plantillas) — probable periodo vacacional.

### Septiembre
- **Cambio de plantilla de las dailies** (~09/09): de "Body/Mind" a formato **TODO/DONE** con navegación ayer-hoy-mañana. Las notas se vuelven más telegráficas y útiles.
- Gestiones familiares: coche **Dacia en taller** (Mitsubishi), notificaciones Seguridad Social y seguro del **padre** (09–11/09).
- Trabajo: **informe de albedo Klip Punt (SA)** validando MODIS vs medidas de campo de un informe externo (10/09); revisión informe DEWA en nueva localización; revisión documento de garantías de módulos (22/09); evaluación remota de ajustes de heliostatos Khi 3048046 y 3049021 (23/09).
- Deporte: inscripción y participación en la **VIII Travesía Río Guadalquivir, Sevilla, 28/09/2025** (aguas abiertas). Cita podólogo para revisión el 01/10 a las 18:15.
- Idea/apunte: [[2026-27-08 Triple Eclipse]] (planificación de eclipses) y añadir patines a [[💲💸💵💰 To Buy]].

### Octubre – Diciembre
- 06/10: **arranque del "Training plan 16W"** (plan de entrenamiento de 16 semanas), que aparece como TODO recurrente desde entonces (con el enlace roto `[[2025-]]`).
- Resto del trimestre: dailies casi vacías, solo plantilla. La actividad del vault se desplaza a notas de proyecto (BESS, Sport).

## Temas transversales 2025
- **Trabajo (Cox / antigua Abengoa, desde 2008)**: óptica de heliostatos CSP (Khi Solar One), herramienta de albedo GEE para ofertas PV internacionales, modelo híbrido PV+BESS, procesado de datos DEWA. Rol: Engineering / Modeling, Sizing & Performance.
- **Patrón de uso de las dailies**: gran parte del contenido son conversaciones completas con ChatGPT/LLM pegadas (preguntas técnicas, redacción de emails). El "contenido propio" suele ser la pregunta inicial entre llaves `{...}`.
- **Deporte/salud**: objetivo de composición corporal, entrenamiento híbrido (gym/bici/carrera/natación), plantillas podológicas, aguas abiertas.
- **Familia**: gemelos (7-8 años), gestiones del padre, comunidad de vecinos en Dos Hermanas, coche Dacia.
- **Búsqueda de empleo**: al menos una candidatura externa (Getinge, mayo); CV digital en Streamlit mantenido.
