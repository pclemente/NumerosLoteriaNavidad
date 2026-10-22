# NumerosLoteriaNavidad

API JSON estática para consultar los premios de la Lotería de Navidad y de la
Lotería del Niño. GitHub Pages, configurado con origen **GitHub Actions**,
publica el contenido de `output/` en
`https://api-loteria.pabloclementeperez.com/output/`.

## Temporada preparada

La configuración activa está fijada de forma explícita para estos sorteos:

| Sorteo | Año esperado | Inicio (Europe/Madrid) | Histórico publicado hasta que haya resultados nuevos |
| --- | ---: | --- | --- |
| Navidad | 2026 | `2026-12-22T09:00:00+01:00` | Navidad 2025 |
| El Niño | 2027 | `2027-01-06T12:00:00+01:00` | El Niño 2026 |

Los dos conjuntos históricos de tres ficheros no se reinician antes del
sorteo. La aplicación puede seguir mostrando el último resumen completo como
histórico. Dos endpoints separados describen la temporada configurada y
devuelven estado `0` durante la pretemporada. El cambio de los datos históricos
y del estado actual solo ocurre cuando RTVE declara el año esperado y ya
contiene al menos un premio tanto en el resumen como en el listado de números.

Los endpoints estables son:

- `LoteriaNavidad.json`, `LoteriaNavidadResumen.json` y
  `LoteriaNavidadStatus.json`.
- `LoteriaNavidadCurrentStatus.json`, estado de Navidad 2026.
- `LoteriaElNino.json`, `LoteriaElNinoResumen.json` y
  `LoteriaElNinoStatus.json`.
- `LoteriaElNinoCurrentStatus.json`, estado de El Niño 2027.

Los clientes deben consultar `CurrentStatus` para saber si el sorteo de la
temporada configurada ha comenzado. Los `Status.json` heredados pertenecen al
mismo histórico que sus ficheros de números y resumen, por lo que pueden seguir
en estado `4` mientras `CurrentStatus` anuncia el siguiente sorteo con estado
`0`.

Cada fichero generado cuando llegan resultados de la nueva temporada incluye
`year`. En ese momento, los cuatro años, los cuatro estados y el año de
`timestamp` deben coincidir. Se conserva la forma de los campos históricos para
los clientes existentes: todos los valores del listado de números siguen
siendo cadenas, incluido `year`; en resumen, estado y `CurrentStatus`, `year`
es un entero.

## Publicación automática

El workflow `publish-results.yml` consulta RTVE cada cinco minutos desde la hora
de inicio en las ventanas del 22 de diciembre y del 6 de enero. En cualquier
otro día termina sin tocar los datos. También admite publicación manual una vez
alcanzada la hora del sorteo; para inspeccionar sin publicar se usa `stage`.
Tras un cambio validado, el mismo job hace commit y despliega un artefacto Pages
limpio; así no depende de que un push hecho por `GITHUB_TOKEN` active otro
workflow. `deploy-pages.yml` publica los cambios manuales enviados a `main`.
Ambos artefactos conservan `CNAME` y la ruta `/output/`.

La publicación falla sin modificar `output/` si ocurre cualquiera de estos
casos:

- el título o el contenedor `viewLoteriaAAAA` no corresponde al año esperado;
- falta alguna de las 20 páginas de rangos, falla HTTPS o cambia el HTML;
- el resumen todavía no tiene premios o el listado está vacío;
- los metadatos no coinciden entre los cuatro JSON;
- una actualización del mismo año retira o reduce un importe, o cambia un
  número ya publicado en el resumen; los premios acumulados sí pueden aumentar.

El productor asigna estado `1` mientras el resumen está incompleto y estado
`2` cuando RTVE ya expone todos los premios, y actualiza `CurrentStatus` en la
misma escritura. Nunca asigna automáticamente los estados oficiales `3` o `4`.
Si los datos validados no han cambiado, tampoco actualiza el timestamp ni crea
un commit. El workflow añade exclusivamente los cuatro JSON del sorteo
seleccionado.

GitHub puede desactivar los workflows programados de repositorios públicos tras
60 días sin actividad. `season-readiness.yml` ejecuta las pruebas el 30 de
noviembre de 2026 y registra una sola evidencia de campaña en
`.github/season-readiness.json`; ese commit evita que el calendario llegue
inactivo al sorteo. Si ese preflight falla o no aparece, hay que reactivar
Actions y ejecutarlo manualmente antes del 22 de diciembre. No toca `output/`
ni publica resultados.

## Comprobación manual y runbook

Crear el entorno e instalar dependencias:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Preparar una candidatura revisable sin tocar los endpoints públicos:

```bash
python lottery_pipeline.py stage navidad --destination .lottery-staging/navidad-2026
python lottery_pipeline.py validate navidad \
  --directory .lottery-staging/navidad-2026 --expected-year 2026
```

Antes de la hora del sorteo o antes de que RTVE cambie a 2026, el primer
comando debe fallar por fecha o por año de origen. Ese fallo es la protección
que mantiene el histórico publicado.

Tras revisar los cuatro JSON, una publicación local exige confirmar el año:

```bash
python lottery_pipeline.py publish navidad \
  --candidate .lottery-staging/navidad-2026 \
  --output output --confirm-year 2026
git diff -- output/LoteriaNavidad.json \
  output/LoteriaNavidadResumen.json output/LoteriaNavidadStatus.json \
  output/LoteriaNavidadCurrentStatus.json
```

Para El Niño se usan `nino` y `2027`. `update` combina las fases anteriores y
es el comando que ejecuta GitHub Actions:

```bash
python lottery_pipeline.py update navidad --confirm-year 2026
python lottery_pipeline.py update nino --confirm-year 2027
```

Cuando exista lista oficial, primero se contrasta con ella. La promoción exige
resumen completo, cobertura por terminaciones, mínimo de números y fondo total
esperado. El estado `4` además requiere una confirmación explícita:

```bash
python lottery_pipeline.py promote navidad \
  --status 4 --confirm-year 2026 --officially-verified
python lottery_pipeline.py validate navidad \
  --directory output --expected-year 2026 --strict-final
```

Estos comandos solo modifican la copia local. Hay que revisar el diff antes de
hacer commit y push. No se deben copiar resultados de otro año ni publicar
ceros o `-1` como si fueran resultados futuros.

Los ficheros históricos conservan su año, timestamp y estado hasta que exista
un sorteo nuevo publicable. El listado heredado de El Niño 2026 omitía el primer
premio `06703` aunque el resumen sí lo contenía. Se reparó únicamente la clave
canónica `"6703": "2000000"`, contrastada con RTVE y con la
[lista oficial de SELAE del 6 de enero de 2026](https://www.loteriasyapuestas.es/f/loterias/documentos/Loter%C3%ADa%20Nacional/listas%20de%20premios/SM_LISTAOFICIAL.A2026.S002.pdf); el
listado vuelve a sumar los 14 millones oficiales por serie y supera la
validación final. La ruta nueva reconoce las filas especiales `p1` con cero
inicial y exige el importe mínimo del premio mayor. Navidad 2025 permanece sin
cambios: su listado histórico suma 13.999.000 euros y no se promocionará ni se
usará como fuente futura sin contrastarlo antes con la lista oficial.

## Estados

`CurrentStatus` expone `year`, `status`, `state`, `message`, `drawDate`,
`timezone` y `error`. Sus transiciones son:

| `status` | `state` | `message` |
| ---: | --- | --- |
| `0` | `not_started` | `El sorteo aún no ha comenzado.` |
| `1` | `in_progress` | `El sorteo está en curso.` |
| `2` | `completed_pending_verification` | `El sorteo ha finalizado y está pendiente de verificación oficial.` |
| `3` | `official_list_available` | `La lista oficial del sorteo está disponible.` |
| `4` | `officially_verified` | `Los resultados del sorteo se han verificado con la lista oficial.` |

`drawDate` y `timezone` permanecen fijos durante toda la temporada. El estado
`3` requiere una lista oficial en PDF y el `4`, que el listado se haya
contrastado con ella.

El endpoint es un fichero estático y cambia al publicar resultados validados,
no por el mero paso del reloj. Si `drawDate` ya ha pasado y todavía devuelve
estado `0`, el cliente debe mostrar que la actualización está pendiente en vez
de asegurar que el sorteo no ha comenzado.

Para preparar otra temporada hay que cambiar los años, fechas y horas de
`NAVIDAD` y `NINO` en `lottery_pipeline.py`, los años del selector del workflow
y sus pruebas. Los cron pueden permanecer iguales si se conservan las horas,
porque `scheduled-draw` solo activa las fechas configuradas.
