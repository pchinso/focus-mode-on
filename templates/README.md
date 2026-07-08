# Plantillas de especificación — Apps de ingeniería Cox

Punto de partida **genérico** para crear el `spec.md` de una aplicación nueva.
Estas plantillas describen *qué decidir y documentar*, no una aplicación
concreta. Sirven para cualquier dominio y cualquier arquitectura: el resultado
de seguirlas es el documento de especificación de **tu** app, que puede
parecerse o no a otras.

> No son una arquitectura impuesta. Donde haya que elegir, la plantilla lista
> las opciones y te pide justificar la tuya.

## Las plantillas

| Plantilla | Qué te ayuda a definir | ¿Reutilizable tal cual? |
| --- | --- | --- |
| [cuestionario_inicio.md](cuestionario_inicio.md) | **Punto de entrada**: brief a rellenar con todo lo necesario antes de empezar | Cuestionario a rellenar |
| [spec_vision.md](spec_vision.md) | Visión, alcance, requisitos, roadmap y criterios de aceptación | Esqueleto a rellenar |
| [spec_architecture.md](spec_architecture.md) | **Elegir** y documentar la arquitectura (varios patrones posibles) | Guía de decisión |
| [spec_visual_id.md](spec_visual_id.md) | Aplicar la identidad visual Cox al software | Casi literal (identidad corporativa) |
| [spec_conventions.md](spec_conventions.md) | **Estándares de entrega obligatorios** (formato de números, idioma del código, documentación, estilo Markdown) | Normativo, casi literal |
| [spec_licensing.md](spec_licensing.md) | Proteger una distribución (si aplica) | Receta reutilizable |
| [markdownlint.jsonc](markdownlint.jsonc) | Config markdownlint a copiar como `.markdownlint.jsonc` en la raíz del proyecto | Copiar tal cual |

> **¿Eres una IA/asistente?** Lee [agents.md](agents.md): contiene el
> procedimiento exacto a seguir para convertir estas plantillas en el `spec.md`
> de la app nueva.

## Proceso para crear el `spec.md` de una app nueva

0. **Rellena el brief** — copia `cuestionario_inicio.md`, complétalo con lo que
   sepas del proyecto. Es el punto de entrada que alimenta todo lo siguiente;
   no hace falta que esté perfecto, pero cuanto más detalles, mejor.
1. **Visión primero** — copia `spec_vision.md` al `spec.md` del proyecto y
   rellena §1 (qué resuelve y para quién) y §2 (alcance V1) a partir del brief.
   No sigas hasta tener esto claro.
2. **Elige la arquitectura** — abre `spec_architecture.md`, recorre el árbol de
   decisión, escoge un patrón (o combina/inventa uno) y **justifícalo**.
   Vuelca el resultado en §4 del spec. Aquí es legítimo apartarse por completo
   de cualquier proyecto anterior.
3. **Identidad visual** — aplica `spec_visual_id.md`; es transversal a toda app
   Cox y apenas cambia entre proyectos.
4. **Convenciones de entrega** — incorpora `spec_conventions.md` (formato de
   números, código en inglés, documentación de usuario y técnica). Son
   **[NORMATIVO]**: aplican siempre, recórtalas solo con justificación.
5. **¿Distribución protegida?** — si la app se reparte como ejecutable/binario
   a terceros, incorpora el esquema de `spec_licensing.md` en §7bis; si no,
   bórralo.
6. **Cierra el spec** — completa requisitos no funcionales, modelo de datos,
   roadmap, criterios de aceptación y riesgos. Cada criterio de aceptación
   debería poder convertirse en una prueba.
7. **Revisa y recorta** — elimina toda sección que no aplique. Un spec con
   huecos `{{...}}` sin resolver no está listo.

## Convenciones de las plantillas

- `{{marcador}}` → texto a sustituir por el contenido de tu proyecto.
- **[NORMATIVO]** → contrato corporativo que conviene mantener entre apps
  (identidad de marca, formato de licencia, contacto de soporte). Cambiarlo es
  una decisión consciente, no un descuido.
- **[ELEGIR]** → punto donde la plantilla ofrece opciones y tú decides.

## Principios de ingeniería (recomendados, no obligatorios)

Buenas prácticas que aplican a casi cualquier app, independientemente de la
arquitectura elegida:

- **Separar cálculo de presentación**: la lógica de negocio debe poder
  probarse sin la interfaz.
- **Validar entradas antes de actuar** y mostrar errores accionables, no
  trazas técnicas.
- **Trazabilidad**: poder reconstruir qué se ejecutó, con qué datos y qué
  versión.
- **Identidad por tokens, no por colores sueltos**: un único punto de tema.
- **Protección proporcional a la amenaza**: no sobre-invertir en blindaje para
  una beta interna.
- **Cada afirmación con una prueba**: si el spec dice que algo funciona,
  debería existir un test que lo demuestre.
