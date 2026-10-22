# NumerosLoteriaNavidad

API JSON estática para consultar los premios de la Lotería de Navidad y de la
Lotería del Niño. GitHub Pages, configurado con origen **GitHub Actions**,
publica el contenido de `output/` en
`https://api-loteria.pabloclementeperez.com/output/`.

## Temporada preparada

La configuración activa está fijada de forma explícita para estos sorteos:

| Sorteo | Año esperado | Fecha (Europe/Madrid) | Histórico publicado hasta que haya resultados nuevos |
| --- | ---: | --- | --- |
| Navidad | 2026 | 22 de diciembre de 2026 | Navidad 2025 |
| El Niño | 2027 | 6 de enero de 2027 | El Niño 2026 |

Los seis ficheros públicos no se reinician antes del sorteo. La aplicación
puede seguir mostrando el último resumen completo como histórico. El cambio de
temporada solo ocurre cuando RTVE declara el año esperado y ya contiene al
menos un premio tanto en el resumen como en el listado de números.

Los endpoints estables son:

- `LoteriaNavidad.json`, `LoteriaNavidadResumen.json` y
  `LoteriaNavidadStatus.json`.
- `LoteriaElNino.json`, `LoteriaElNinoResumen.json` y
  `LoteriaElNinoStatus.json`.

Cada fichero generado para la nueva temporada incluye `year`. Los tres años,
los tres estados y el año de `timestamp` deben coincidir. Se conserva la forma
de los campos históricos para los clientes existentes: todos los valores del
listado de números siguen siendo cadenas, incluido `year`; en resumen y estado,
`year` es un entero.

## Publicación automática

El workflow `publish-results.yml` consulta RTVE cada cinco minutos en las
ventanas del 22 de diciembre y del 6 de enero. En cualquier otro día termina
sin tocar los datos. También admite publicación manual una vez alcanzada la
fecha del sorteo; para inspeccionar sin publicar se usa `stage`.
Tras un cambio validado, el mismo job hace commit y despliega un artefacto Pages
limpio; así no depende de que un push hecho por `GITHUB_TOKEN` active otro
workflow. `deploy-pages.yml` publica los cambios manuales enviados a `main`.
Ambos artefactos conservan `CNAME` y la ruta `/output/`.

La publicación falla sin modificar `output/` si ocurre cualquiera de estos
casos:

- el título o el contenedor `viewLoteriaAAAA` no corresponde al año esperado;
- falta alguna de las 20 páginas de rangos, falla HTTPS o cambia el HTML;
- el resumen todavía no tiene premios o el listado está vacío;
- los metadatos no coinciden entre los tres JSON;
- una actualización del mismo año retira o reduce un importe, o cambia un
  número ya publicado en el resumen; los premios acumulados sí pueden aumentar.

El productor asigna estado `1` mientras el resumen está incompleto y estado
`2` cuando RTVE ya expone todos los premios. Nunca asigna automáticamente los
estados oficiales `3` o `4`. Si los datos validados no han cambiado, tampoco
actualiza el timestamp ni crea un commit. El workflow añade exclusivamente los
tres JSON del sorteo seleccionado.

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

Antes de la fecha del sorteo o antes de que RTVE cambie a 2026, el primer
comando debe fallar por fecha o por año de origen. Ese fallo es la protección
que mantiene el histórico publicado.

Tras revisar los tres JSON, una publicación local exige confirmar el año:

```bash
python lottery_pipeline.py publish navidad \
  --candidate .lottery-staging/navidad-2026 \
  --output output --confirm-year 2026
git diff -- output/LoteriaNavidad.json \
  output/LoteriaNavidadResumen.json output/LoteriaNavidadStatus.json
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

- `0`: el sorteo todavía no ha comenzado.
- `1`: el sorteo está en curso y los premios se incorporan progresivamente.
- `2`: el origen contiene el resumen completo, pendiente de lista oficial.
- `3`: existe lista oficial en PDF.
- `4`: listado contrastado con la lista oficial.

Para preparar otra temporada hay que cambiar los años y fechas de `NAVIDAD` y
`NINO` en `lottery_pipeline.py`, los años del selector del workflow y sus
pruebas. Los cron pueden permanecer iguales porque `scheduled-draw` solo activa
las fechas configuradas.
