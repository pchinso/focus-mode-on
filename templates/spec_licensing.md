# Licenciamiento y protección para distribución beta

> Plantilla reutilizable. Esquema de protección para repartir ejecutables o
> binarios a probadores/colaboradores. Aplícalo solo si la app se distribuye
> fuera del equipo; si no, omite esta plantilla.

## 1. Marco realista  **[LEER PRIMERO]**

Un ejecutable Python (PyInstaller) **no es blindable**: el bytecode se puede
extraer y descompilar. El objetivo para una beta no es criptografía
inviolable, sino **disuasión razonable + trazabilidad**: que caduque, que no
funcione copiada, y que toda copia/resultado sea atribuible a una persona.

Para distribución a **clientes externos** valorar además ofuscación (PyArmor)
y/o validación online — fuera del alcance de esta plantilla.

## 2. Esquema recomendado (2 + 3 + 4 + 5)

| # | Mecanismo | Protege contra |
| --- | --- | --- |
| 2 | **Licencia firmada Ed25519** | Falsificación; permite caducidad por probador sin recompilar |
| 3 | **Vinculación a máquina** | Copia a otro equipo |
| 4 | **Anti-retroceso de reloj** | Atrasar la fecha para evitar la caducidad |
| 5 | **Marca de agua** (licenciatario en UI/About/informes) | Compartir capturas/resultados |

## 3. Cómo funciona  **[NORMATIVO]**

- **Par de claves Ed25519**: la **pública** va embebida en el binario
  (`PUBLIC_KEY_HEX`); la **privada** la custodia el emisor y **nunca** se
  distribuye ni se versiona. Extraer la pública no permite falsificar.
- **`<app>.lic`**: JSON
  `{licensee, company, email, machine_id, issued, expires, product}` + firma
  Ed25519 en base64. Serialización canónica (claves ordenadas) para firmar.
- **`machine_id`**: hash de hostname + identificador estable de la máquina
  (en Windows, `MachineGuid` del registro).
- **Caducidad**: campo `expires`; aviso al usuario cuando quedan ≤ N días,
  bloqueo al vencer.
- **Anti-retroceso**: un fichero local guarda el último uso sellado con HMAC;
  si el reloj retrocede más de la tolerancia, se bloquea. *(Cuidado al
  implementar: sella y verifica el MISMO valor entero — no el float redondeado
  en un lado y el truncado en otro, o el HMAC nunca cuadra.)*
- **Aplicación del gate**: solo en el ejecutable empaquetado (`sys.frozen`) o
  con variable de entorno de override. En desarrollo no bloquea (tests y
  trabajo diario), pero si hay `.lic` se lee y se muestra igual.
- **Alcance**: proteger la **GUI** (donde está el valor de uso). Los motores
  CLI quedan sin gate en beta; endurecerlos es decisión aparte.

## 4. Marca de agua

El nombre del licenciatario aparece en: barra de estado, ventana **Acerca de**
y pie de los informes generados. Hace cada copia trazable a una persona.

## 5. Ventana "Acerca de"  **[NORMATIVO]**

Debe mostrar: versión de la app, **datos de contacto de soporte**, estado y
validez de la licencia (licenciatario, fechas, días restantes) y el **ID de
esta máquina** con botón para copiarlo.

Contacto de soporte (Cox Engineering — Modeling, Sizing & Performance):
```text
Pablo Climent Sánchez
Engineering / Modeling, Sizing & Performance
pablo.climent@grupocox.com · (+34) 654 543 583
```

## 6. Flujo de activación (documentar en el README de cada app)

**Probador**

1. Arranca la app; si no hay licencia válida, el diálogo muestra el **ID de
   esta máquina** (también disponible en "Acerca de" o por un comando
   `--machine-id` que, si el binario no tiene consola, lo escriba a un fichero).
2. Envía ID + nombre + empresa a soporte.
3. Recibe `<app>.lic` y lo copia **junto al ejecutable**; reinicia.

**Emisor**
Un script generador (que NO se distribuye) firma la licencia con la clave
privada, dados nombre, empresa, email, ID de máquina y validez (`--days N` o
`--expires YYYY-MM-DD`). Debe validar que la privada corresponde a la pública
embebida antes de emitir.

## 7. Custodia de la clave privada  **[CRÍTICO]**

- Guardar **fuera del control de versiones** (ignorar `*.pem`) y con copia de
  seguridad segura aparte. Restringir quién la tiene.
- Guard de empaquetado: una prueba debe fallar si aparece algún `.pem` dentro
  del paquete distribuible.
- Si se pierde o filtra: generar par nuevo, actualizar la clave pública
  embebida, recompilar y reemitir todas las licencias.

## 8. Limitaciones a comunicar

Protección **disuasoria, no inviolable**. Adecuada para beta entre
colaboradores identificados. No sustituye a un acuerdo de uso/NDA.

## 9. Pruebas mínimas a replicar

- Par de claves coherente con la app · licencia válida OK.
- Rechazo: firma manipulada, máquina distinta, caducada, ausente.
- Detección de retroceso de reloj.
- Ventana About construye con/sin licencia (claro y oscuro).
- Guard: la clave privada no está dentro del paquete.
- E2E sobre el binario: con licencia arranca; sin licencia, diálogo de bloqueo.
