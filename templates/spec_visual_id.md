# Identidad visual Cox aplicada a software

> Plantilla reutilizable y transversal a cualquier app Cox. Traduce el
> "Universal Visual Identity System" de Cox a tokens y reglas de UI. Es casi
> literal entre proyectos: la marca no cambia, solo cómo la aplicas.

## 1. Paleta corporativa  **[NORMATIVO — colores invariantes]**

### Primarios

| Rol | Nombre | Hex | Uso |
| --- | --- | --- | --- |
| Primario | **Planet Blue** | `#283198` | Cabeceras, sidebar, botones primarios, header de tablas |
| Vertical agua | Water Turquoise | `#2CB8C7` | Acentos, estados informativos, gradiente |
| Vertical energía | **Energy Coral** | `#ED696A` | Énfasis, alertas suaves, gradiente |

### Secundarios

Light Water Turquoise `#9FD6DF` · Light Energy Coral `#F5ACA4` ·
Dark Water Turquoise `#11717B` · Dark Energy Coral `#A13838` ·
Angel Blue `#BDC5E3` · Moon Grey `#EAEDED` · Night Grey `#43464F` ·
Blanco `#FFFFFF` · Negro `#000000`.

### Reglas de marca

- Gradiente corporativo Planet Blue → Water Turquoise → Energy Coral (header).
- En contexto **energía** se prioriza Planet Blue + Energy Coral; en **agua**,
  Planet Blue + Water Turquoise. Nunca al revés.
- Logo full-color sobre fondo claro; logo blanco sobre Planet Blue / gradiente
  / fondo oscuro. Mínimo 100 px de ancho en digital. Nunca deformar, inclinar
  ni recolorear.

## 2. Tokens de interfaz (no usar colores sueltos)  **[NORMATIVO]**

Centralizar **todo** en un único punto de tema (un `theme.py`, un fichero de
variables CSS, un design-token JSON… según tu stack). Los componentes leen
tokens, no literales. Definir dos paletas funcionales (claro y oscuro) sobre los
mismos nombres de token. Conjunto de tokens mínimo sugerido:

```text
BLUE_DEEP, BLUE_DARKER, BG_APP, BG_PANEL, SURFACE, SURFACE_ALT,
ROW_EVEN, ROW_IMPORTANT, INPUT_BG, INPUT_BORDER, HOVER_BG, SELECT_BG,
NAV_BG, NAV_HOVER, LOG_BG, BORDER, BORDER_SOFT,
TEXT_MAIN, TEXT_SOFT, TEXT_LINK, TABLE_TEXT, GRID_LINE, CHART_BG
```

- Un `set_mode("light"|"dark")` (o equivalente) rellena los tokens; el modo se
  persiste (preferencias de usuario) y se aplica **antes** de construir la UI.
- Los colores **primarios y secundarios Cox son invariantes** entre modos;
  solo cambian los tokens funcionales (fondos, bordes, textos).

## 3. Modo claro / oscuro

- Control de cambio de modo accesible (p. ej. botón en el header); guarda la
  preferencia y la aplica.
- **Regla anti-regresión**: ningún componente de UI debe fijar un fondo blanco
  (`white` / `#fff`) hardcodeado — rompe el modo oscuro. Recomendado: un test o
  linter que escanee la UI y falle si reaparece un color fuera de los tokens.

## 4. Tipografía  **[NORMATIVO]**

- **Primaria**: Red Hat Display (Regular texto, Bold títulos/énfasis, Black
  énfasis fuerte, Italic para fórmulas/extranjerismos). **Empaquetar la fuente**
  (licencia OFL) con la app y registrarla al arrancar; fallback a Segoe UI.
- **Email / casos especiales**: Arial.
- No usar mayúsculas sostenidas; no justificar texto.

## 5. Gráficas y visualizaciones

- Estilo derivado de los tokens del tema activo, de modo que las gráficas
  siguen el modo claro/oscuro (en matplotlib, vía `rcParams`; en web, vía
  variables CSS / config del motor de gráficas).
- Paleta de series = primarios + secundarios Cox (con variante para modo
  oscuro si los colores claros pierden contraste).
- Fondo de figura = `CHART_BG`; rejilla = `GRID_LINE`; líneas de umbral u
  objetivo en Energy Coral discontinuo.

## 5bis. Formato de números (presentación)  **[NORMATIVO]**

En UI, gráficas e informes, los números decimales se muestran a **2 decimales**
(`1.23`) y **siempre con su unidad en celda/etiqueta adyacente**, no dentro del
número. El redondeo es solo de presentación; cálculo y persistencia usan la
precisión completa. Regla canónica y excepciones en `spec_conventions.md`.

## 6. Componentes con sello Cox (patrones reutilizables)

Ejemplos de componentes que dan el "look & feel" Cox; adáptalos a tu stack:

- Cabecera con gradiente corporativo.
- Navegación con elemento activo en Planet Blue.
- Tablas con cabecera Planet Blue, filas alternas y coloreado de estados
  (ok/aviso/error).
- Logo en formato vectorial (SVG) embebido.
- Controles de marca (toggles, botones) usando los acentos Water Turquoise /
  Energy Coral según el contexto (agua / energía).

## 7. Checklist de cumplimiento

- [ ] Un único punto de tema; cero colores hardcodeados en componentes.
- [ ] Tokens claro y oscuro completos; guard anti-regresión activo.
- [ ] Red Hat Display empaquetada y registrada; fallback definido.
- [ ] Gradiente y reglas de logo respetados.
- [ ] Gráficas tematizadas desde los tokens.
- [ ] Diálogos y superficies usando tokens (`SURFACE`/`TEXT_MAIN`), no `white`.
