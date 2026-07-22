# Estado, método y ruta del proyecto

Actualizado: 21 de julio de 2026.

Este es el documento descriptivo vivo de `linux-rig-tools`. Explica qué se ha
hecho, por qué se hizo, qué evidencia existe, qué falta y cómo se controla el
riesgo. La hoja de ruta general sigue en [ROADMAP.md](ROADMAP.md). Si este
documento y el código discrepan sobre el estado actual, se debe comprobar el
código, las capturas, las pruebas y Git antes de concluir cuál está vigente.

## Resumen ejecutivo

El proyecto busca recuperar desde Linux el control de componentes que hoy
dependen de aplicaciones de Windows. El primer objetivo es el controlador USB
integrado en la placa NZXT N9 Z890, identificado como `1e71:2023`. Después
siguen el AIO Cooler Master, la matriz LED del chasis y los demás dispositivos
sin soporte.

El avance actual ya supera la fase de reconocimiento. Existe un laboratorio
Windows reproducible, capturas USB aisladas, una parte importante del protocolo
de iluminación fija del N9 está decodificada y la primera escritura física
desde Linux ya fue reversible. También hay dos herramientas generales seguras:

- `nzxt-n9 status`, que abre el dispositivo en solo lectura y decodifica su
  heartbeat.
- `nzxt-n9 encode`, que construye tramas en memoria y nunca las transmite.

El 21 de julio de 2026 Linux completó dos ciclos de iluminación integrada de la
N9. En ambos cambió al instante a rojo tenue y restauró al instante su cian
habitual mediante la trama que CAM identifica como blanco `#FFFFFF`. La
apariencia cian del blanco no depende del ángulo ni de la fotografía. Es el
comportamiento habitual de esa zona desde el estado predeterminado. Los
ventiladores siguieron girando igual durante los cuatro cambios. Esto demuestra
control físico, reversión y repetibilidad en el hardware de referencia.

H1 a H4 del primer hito quedaron cerradas. El artefacto de H4 es el arnés de
laboratorio `tools/nzxt-n9/bin/nzxt-n9-first-write-lab`, con pruebas offline y
evidencia descriptiva. No es una API genérica y no está instalado en el
sistema.

Desde el estado actual faltan:

- Seis de las siete macroetapas del objetivo final del proyecto, control útil
  desde Linux de todo el hardware objetivo, con integración, empaquetado y
  aportes a proyectos upstream. La Macroetapa 1, iluminación fija del N9, ya
  está completa.

## Cómo se clasifican las afirmaciones

- **Verificado:** existe una captura, descriptor, prueba, estado del sistema o
  resultado reproducible que respalda la afirmación.
- **Inferencia:** la evidencia favorece una explicación, pero no la demuestra
  de forma única.
- **Desconocido:** la evidencia actual no permite responder todavía.

Esta separación es importante. Una coincidencia entre bytes y una acción de
CAM no convierte por sí sola esos bytes en una especificación segura para
escribir al dispositivo.

## El problema que estamos resolviendo

La placa no expone canales PWM de ventiladores mediante las interfaces Linux
habituales. Los headers de ventiladores, parte del RGB y posiblemente otras
funciones están detrás del controlador USB `1e71:2023`. NZXT CAM puede manejarlo
en Windows, pero liquidctl y OpenRGB no soportan este PID ni su protocolo de
reportes de 512 bytes.

El equipo también contiene estos objetivos:

| Componente | Identidad | Aplicación de Windows | Resultado deseado |
| --- | --- | --- | --- |
| Controlador NZXT N9 Z890 | `1e71:2023` | NZXT CAM | RGB, telemetría, ventiladores, bomba y curvas |
| Cooler Master MasterLiquid Core Nex Digital | `2516:0232` | MasterCTRL | Bomba, ventiladores, ARGB y pantalla digital |
| Matriz LED del chasis | `ff00:020c` | Suite del fabricante | Reloj, reloj de arena y animaciones |
| Compuesto USB del chasis | `26ce:0a09` | Por identificar | Determinar si transporta pantalla, audio o control auxiliar |
| RGB de la Zotac RTX 5060 Ti | Por confirmar | FireStorm o Spectra | Control desde OpenRGB u otro upstream apropiado |
| Teclado Evision | `320f:5000` | Software del fabricante | Completar el soporte de su familia en OpenRGB |

El objetivo no es reemplazar liquidctl, OpenRGB o CoolerControl. El repositorio
sirve para descubrir, probar y demostrar protocolos nuevos. Cuando el soporte
sea estable debe integrarse en el proyecto upstream adecuado.

## Lo que se ha hecho hasta ahora

### 1. Inventario y base del repositorio

**Por qué:** antes de tocar hardware era necesario saber qué controladores
existían, cuáles tenían soporte y cuáles requerían ingeniería inversa.

**Qué se hizo:**

- Se creó el monorepo público con herramientas independientes.
- Se documentó el equipo de referencia en [HARDWARE.md](HARDWARE.md).
- Se construyó `rig-diagnose` para inventariar hardware sin modificarlo.
- Se construyó `rig-profiles` para perfiles de CPU y límite de potencia NVIDIA.
- Se añadieron instaladores, reglas udev y empaquetado inicial para Arch y
  Debian.
- Se creó la [guía de capturas](CAPTURE-GUIDE.md).

**Qué obtuvimos:** una base reutilizable para que el trabajo no dependa de una
sola máquina ni de comandos recordados de una conversación.

### 2. Laboratorio Windows para observar las aplicaciones oficiales

**Por qué:** los protocolos no están documentados. La fuente de verdad práctica
es observar a las aplicaciones oficiales hablando con el hardware real.

**Qué se hizo:**

- Se diagnosticó el Windows original del PNY. Una actualización interrumpida
  dejó `wininit.exe` fallando con `CRITICAL_PROCESS_DIED`.
- Se abandonó su reparación cuando quedó claro que una VM limpia produciría el
  mismo tráfico USB necesario para este proyecto.
- Se preparó QEMU/KVM, libvirt, TPM virtual, Secure Boot, red NAT y una VM de
  Windows 11 llamada `win11-cap`.
- Se instalaron NZXT CAM 4.76.5 y MasterCTRL 1.5.2.241.
- Se habilitó la captura desde Linux mientras el dispositivo estaba asignado a
  la VM.

**Qué obtuvimos:** un laboratorio permanente donde se puede cambiar una sola
opción en CAM y observar exactamente qué tráfico USB genera.

**Estado actual verificado:** la VM `win11-cap` existe. Durante ambos ciclos
físicos de primera escritura del 21 de julio de 2026 permaneció apagada y el N9
perteneció a Linux. Mientras la VM está apagada no hay Guest Agent que deba
responder. Los cuatro dispositivos USB principales estaban visibles desde
Linux y no asignados a la VM.

### 3. Capturas controladas del N9

**Por qué:** una captura larga con muchas acciones mezcla causas y efectos. Para
deducir un protocolo se necesita cambiar una sola variable por vez.

**Qué se hizo:**

- Se separaron enumeración, arranque del servicio, apertura de CAM, entrada a
  Iluminación, brillo, color y otros gestos.
- Se usaron puntos exactos de brillo y repeticiones para intentar refutar las
  primeras fórmulas.
- Se capturaron colores primarios, colores mixtos y permutaciones como
  `#804020` y `#408020`.
- Se repitieron estados para comprobar igualdad byte por byte.
- Se registraron por separado las acciones humanas y la evidencia del PCAP.

**Qué obtuvimos:** una colección D1 a D24 que permite comparar cambios pequeños
sin atribuir a un gesto paquetes causados por otro dispositivo o por una acción
anterior.

### 4. Estructura HID y mapa parcial del protocolo

**Por qué:** antes de cualquier escritura hay que saber si el primer byte es un
Report ID, el tamaño exacto del buffer y la ruta correcta de transporte.

**Qué se hizo:**

- Se leyó el descriptor HID de 150 bytes desde sysfs, sin abrir el dispositivo
  para escritura.
- Se decodificaron Report Size, Report Count y los Report ID de entrada y
  salida.
- Se cruzó el descriptor con las tramas de CAM.
- Se documentó el mapa de opcodes observados.

**Qué obtuvimos, verificado:**

- Los reportes son numerados.
- Cada reporte ocupa 512 bytes, un Report ID y 511 bytes de payload.
- `0x26` es un Report ID de salida.
- La trama capturada que comienza `26 04 20 00` ya es el buffer completo.
- No se debe anteponer `0x00`, duplicar `0x26` ni recortar el primer byte.
- El transporte observado es interrupt OUT, no Feature report.

### 5. Decodificación de iluminación fija

**Por qué:** el modo `Fixed` es la superficie más pequeña y controlable para
demostrar escritura real sin empezar por ventiladores, bomba o firmware.

**Qué se hizo:**

- Se compararon tramas de blanco, rojo, verde, azul, magenta y colores mixtos.
- Se probaron modelos lineales y no lineales de componente y brillo.
- Se buscaron puntos que discriminaran entre fórmulas competidoras.
- Se validó un codificador offline contra capturas guardadas.

**Qué obtuvimos, verificado para CAM 4.76.5, Canal 6 y brillo 7 por ciento:**

- La trama de datos empieza con `26 04 20 00`.
- Después aparecen 49 tripletas en orden GRB.
- El resto del buffer se rellena con ceros.
- CAM envía después una trama de commit `26 06` fija.
- El codificador reproduce nueve capturas completas byte por byte al 7 por
  ciento.
- La personalización de `Fixed` expone 49 rectángulos seleccionables, 17 en el
  lateral izquierdo, 17 en el tramo horizontal inferior y 15 en el lateral
  derecho.
- D26 demostró que CAM restaura un vector personalizado guardado y transmite
  49 tripletas independientes con la misma cabecera y el mismo commit.
- D27 demostró que el primer rectángulo superior izquierdo corresponde a la
  primera tripleta. Al elegir rojo, solo esa tripleta cambió de `00 00 89` a
  `00 89 00` y las otras 48 quedaron idénticas.

**Lo que sigue siendo inferencia o desconocido:**

- Las 49 tripletas corresponden a 49 rectángulos controlables de la cubierta,
  pero no prueban que cada rectángulo represente un único LED físico.
- Solo la correspondencia exacta del primer rectángulo está demostrada. El
  recorrido completo de 17, 17 y 15 tiene evidencia visual fuerte, pero faltan
  anclas controladas para probar las otras 48 posiciones.
- `20 00` todavía no tiene una semántica demostrada.
- La interfaz de CAM decía Canal 6, pero no se ha demostrado dónde se codifica
  el canal.
- Nueve colores están validados al 7 por ciento y dos colores mixtos están
  validados al 25 y 50 por ciento. Los demás cruces entre color y brillo todavía
  son una extrapolación que puede diferir de CAM por un nivel.

La evidencia detallada está en
[NZXT-N9-CAM-LIGHTING.md](NZXT-N9-CAM-LIGHTING.md).

### 6. Herramientas seguras ya disponibles

**`nzxt-n9 status`:** localiza el dispositivo por VID y PID, abre `/dev/hidrawN`
con `O_RDONLY` y decodifica reportes `ff 03`. Nunca llama a `os.write`.

**Resultado:** se demostró que `ff 03` es un heartbeat con un contador, no
telemetría de temperatura, RPM o bomba. Esto corrigió una hipótesis anterior y
evita construir un lector de sensores sobre bytes que no son sensores.

**`nzxt-n9 encode`:** recibe un color y un porcentaje, construye una trama de
512 bytes en memoria y la imprime en hexadecimal. Nunca abre `/dev/hidraw`.

**Resultado:** tenemos un generador reproducible y comprobable antes de permitir
que un solo byte salga hacia el dispositivo.

**Arnés cerrado de primera escritura:** `tools/nzxt-n9/bin/nzxt-n9-first-write-lab`
es una herramienta de laboratorio limitada a `preflight`, `apply-red`,
`restore-white` y ayuda. Solo envía las tramas congeladas D12 rojo y D11 blanco
de CAM al 7 por ciento, más el commit observado. Resuelve el dispositivo por
HID_ID exacto, descriptor y major:minor, con segunda verificación después de
abrir y antes de escribir. No acepta color, brillo, canal, Report ID, ruta
hidraw, número de LED, payload ni bytes arbitrarios. No está cableado en
`install.sh`, PKGBUILD ni paquetes Debian.

**Resultado físico:** rojo y restauración funcionaron dos veces con el mismo
resultado. Las pruebas offline del arnés no abren hardware real.

### 7. Borradores para upstream

**Por qué:** el objetivo no termina en una herramienta privada. El conocimiento
debe llegar a liquidctl, OpenRGB y, si aplica, liquidtux.

**Qué se hizo:** existe un borrador privado de driver para liquidctl y una nota
de dispositivo para OpenRGB. La función de transmisión está deshabilitada.

**Qué esperamos obtener:** estos borradores deben reconciliarse con la evidencia
ya validada en dos ciclos físicos y completar el alcance necesario antes de
publicarse. Así reducen el trabajo para una contribución revisable por los
mantenedores.

No están listos para publicar. La primera escritura ya ocurrió dos veces. Ahora
falta alinear los borradores con esa evidencia y cerrar el alcance pendiente
antes de proponerlos aguas arriba.

### 8. Incidente de iluminación del radiador

**Hechos verificados por observación humana:**

- Los ventiladores del radiador nunca dejaron de girar.
- Solo se apagó su iluminación.
- Reiniciar la torre completa restauró la iluminación.

**Inferencia fuerte:** el RGB quedó en un estado transitorio o incompleto y el
reinicio completo reinicializó el controlador o restauró un perfil válido.

**Lo que no sabemos:** no existe una captura aislada del momento exacto en que
se apagó la iluminación, por lo que no se puede atribuir a una acción concreta
de CAM.

**Valor para la seguridad:** un reinicio completo de la torre queda demostrado
como vía de recuperación para un bloqueo de iluminación. No sustituye una
reversión por protocolo y no demuestra que pueda recuperar cualquier fallo del
controlador.

### 9. Primera escritura física desde Linux

**Hechos verificados el 21 de julio de 2026:**

- El preflight resolvió `/dev/hidraw4` por HID_ID
  `0003:00001E71:00002023` y comprobó un descriptor de 150 bytes con Output
  Report ID `0x26`.
- La línea base térmica fue 66 grados Celsius, por debajo de la puerta de 85
  grados Celsius.
- Linux envió una trama fija de rojo `#FF0000` al 7 por ciento y el commit
  `26 06`, ambos de 512 bytes.
- La iluminación integrada de la cubierta de la N9 cambió a rojo tenue al
  instante. Los aros de los ventiladores y la RAM conservaron sus estados.
- Ismael confirmó físicamente que todos los ventiladores siguieron girando
  igual y que lo único que cambió fue esa zona de la placa.
- Linux envió después la trama de CAM `#FFFFFF` al 7 por ciento y su commit.
  La zona volvió al instante al cian tenue habitual que CAM etiqueta como
  blanco.
- Ismael confirmó que esa diferencia es persistente desde el estado
  predeterminado y no depende del ángulo de observación ni de la fotografía.
  El rojo se aproxima razonablemente al color esperado.
- Las temperaturas observadas durante el ciclo permanecieron entre 47 y 75
  grados Celsius, siempre por debajo de la puerta de 85 grados Celsius.
- Después de la reversión, el dispositivo siguió enumerado con la identidad y
  el descriptor esperados.
- El ciclo completo se repitió desde el cian restaurado. El segundo rojo volvió
  a aparecer al instante, no alteró ningún otro comportamiento visible y la
  segunda restauración devolvió al instante el cian habitual.
- La segunda línea base fue 49 grados Celsius, la lectura posterior al rojo fue
  50 grados Celsius y la lectura posterior a la restauración fue 69 grados
  Celsius.

**Límite verificado:** una lectura posterior no recibió un heartbeat dentro de
una ventana de cinco segundos. El timeout no demuestra que el heartbeat haya
cesado, pero tampoco permite contarlo como confirmación posterior. La
enumeración, la reversión física y la temperatura sí quedaron confirmadas.

**Qué demostró:** `26 04` seguido de `26 06` controla desde Linux varias zonas
integradas de iluminación de la N9. El color se aplica inmediatamente, puede
revertirse por el mismo protocolo sin reiniciar la torre y el ciclo produce el
mismo resultado al repetirlo desde el estado restaurado.

**Qué sigue abierto:** la prueba no establece que las 49 tripletas correspondan
a 49 LED físicos ni mapea cada tripleta a una zona. La repetibilidad física ya
está demostrada con dos ciclos. El arnés de laboratorio y sus pruebas offline
quedan integrados en la rama como cierre de H4.

**Interpretación actual de color:** la trama de blanco contiene valores iguales
para los tres componentes, `4a 4a 4a`, por lo que el sesgo cian no se origina en
una desigualdad entre los bytes enviados. Puede proceder de la respuesta
espectral de los LED, su calibración eléctrica, el difusor o diferencias entre
canales a brillo bajo. Estas causas son inferencias y todavía no se han medido.

### 10. Separación entre el estado guardado por CAM y el estado físico

**Hecho visual verificado el 21 de julio de 2026:** CAM quedó en `Fixed`, verde
`#00FF00` al 100 por ciento y sin personalización por zonas. La N9 volvió a
Linux y recibió la trama blanca congelada al 7 por ciento. Ismael confirmó el
cian habitual y ventiladores normales. Al conectar nuevamente la N9 a la misma
VM, con CAM abierto y sin hacer clic ni cambiar controles, la placa volvió por
sí sola a verde al 100 por ciento.

Esto demuestra que CAM conserva y reaplica su estado actual cuando el
dispositivo reaparece durante la misma sesión. También demuestra que el valor
`#7F7F7F` mostrado al abrir CAM era estado propio de CAM y no contaminó las
escrituras completas de rojo y blanco realizadas desde Linux. El arranque que
mostró nuevamente `#7F7F7F` es compatible con persistencia entre sesiones, pero
esa parte no se ejecutó como prueba controlada.

Un PCAP abierto durante la búsqueda manual de verde al 100 por ciento quedó
clasificado como exploratorio y contaminado. Incluyó clics, borrados,
correcciones y valores intermedios no controlados. No se usa para validar ni
refutar el modelo de `Fixed`.

### 11. Primera prueba cruzada de color y brillo

**Hecho verificado el 21 de julio de 2026:** CAM se preparó fuera de captura en
`Fixed`, sin personalización por zonas, con `#5A23F4` y brillo individual del
Canal 6 al 49 por ciento. Durante una captura anunciada y exclusiva, Ismael
pulsó una sola vez Flecha derecha para llegar al 50 por ciento. Confirmó el 50
por ciento y ventiladores normales.

La tesis registrada antes de medir permitía únicamente cuatro resultados GRB:
`16 3f b2`, `16 40 b2`, `17 40 b2` o `17 40 b3`. El PCAP contiene un único par
de escrituras salientes. La trama `26 04` repite `17 40 b2` exactamente 49
veces y la trama `26 06` completa el cambio 3.931 ms después. Las dos
transferencias terminaron con estado exitoso y no existen escrituras
competidoras del N9.

La tesis unificada supera esta prueba discriminante y su intervalo compatible
de cuantización se reduce de aproximadamente `0.306365 a 0.467255` a
`0.386776 a 0.427699`. Esto es evidencia fuerte a favor del modelo, no una
demostración universal.

### 12. Segunda prueba cruzada de color y brillo

**Hecho verificado el 21 de julio de 2026:** CAM se preparó fuera de captura en
`Fixed`, sin personalización por zonas, con `#0E50AD` y brillo individual del
Canal 6 al 24 por ciento. Durante una captura anunciada y exclusiva, Ismael
pulsó una sola vez Flecha derecha para llegar al 25 por ciento. Confirmó el 25
por ciento y ventiladores normales.

La tesis registrada antes de medir permitía únicamente cuatro resultados GRB:
`26 03 5a`, `26 04 5a`, `27 04 5a` o `27 04 5b`. El PCAP contiene un único par
de escrituras salientes. La trama `26 04` repite `27 04 5b` exactamente 49
veces y la trama `26 06` completa el cambio 2.982 ms después. Las dos
transferencias terminaron con estado exitoso y no existen escrituras
competidoras del N9.

La tesis unificada supera también D24 y su intervalo compatible queda en
`0.4173921478326008 <= t < 0.4276988003512372`. El modelo ya superó cruces
controlados con colores mixtos al 25 y 50 por ciento, además de las series
anteriores de color y brillo.

### 13. Escritura Linux predicha para un estado nunca capturado

**Hecho verificado el 21 de julio de 2026:** el modelo construyó `#FFD000` al
40 por ciento, una combinación nunca capturada de CAM. La trama usa el triple
GRB `89 a9 00` repetido 49 veces y tiene SHA-256
`c8e1db05b544d92df8815e82e64dba2d23aa92f71d50861b58eba368b6d62138`.

El checkpoint `65be586` pasó 35 pruebas offline y una revisión independiente
sin hallazgos. Un primer intento sin privilegios terminó en permiso denegado
antes de abrir `hidraw` y escribió cero bytes. La repetición mediante sudo abrió
la N9 validada y escribió la trama amarilla y el commit. Ismael observó un color
amarillo o dorado inmediato y confirmó que todos los ventiladores siguieron
girando normalmente.

La restauración blanca al 7 por ciento devolvió el cian habitual y mantuvo los
ventiladores normales. Al reconectar la N9 a la VM, CAM reaplicó automáticamente
`#0E50AD` al 25 por ciento. Las temperaturas de las dos escrituras fueron 62 C
y 75 C, debajo del límite de 85 C.

**Conclusión:** el modo `Fixed` global queda cubierto con evidencia suficiente
para implementar en Linux cualquier color RGB y cualquier brillo entero de 0 a
100. El codificador genérico ya existe offline. Todavía no existe una ruta
genérica de escritura ni una interfaz visual, porque el arnés físico conserva
solo tres estados congelados. La estructura de personalización por zonas ya
está demostrada como un vector completo de 49 tripletas GRB y la primera zona
está mapeada exactamente. Aún falta validar anclas del recorrido completo y la
transformación de color y brillo por zona antes de exponer control arbitrario.

## Técnicas usadas y qué esperamos obtener de cada una

| Técnica | Para qué se usa | Qué ha producido | Qué esperamos obtener después |
| --- | --- | --- | --- |
| Inventario con sysfs, `lsusb`, hidraw y sensores | Identificar el hardware real y sus límites | VID, PID, interfaces y ausencia de PWM Linux | Detección estable sin depender de números de bus o hidraw |
| QEMU/KVM y passthrough USB | Ejecutar las aplicaciones oficiales contra el hardware real | Laboratorio Windows reproducible | Capturar Cooling, efectos y dispositivos restantes |
| `usbmon`, tshark y PCAP | Observar bytes sin escribir desde Linux | Handshake, heartbeat y tramas de iluminación | Descubrir telemetría, canales, efectos y controles |
| Experimentos diferenciales | Relacionar una acción con una diferencia de tráfico | Series D1 a D27 con acciones aisladas | Reducir falsos positivos y establecer causalidad más fuerte |
| Repetición byte por byte | Separar coincidencias de comportamiento reproducible | Repetición de brillo y colores mixtos | Tramas doradas para pruebas automáticas |
| Pruebas discriminantes | Refutar fórmulas que coinciden por accidente | El modelo sobrevivió D22, D24 y una escritura física inédita D25. D26 y D27 aislaron estado y posición por zona | Diseñar la ruta genérica de escritura global y completar anclas por zona |
| Análisis del descriptor HID | Resolver formato y dirección de reportes | Report ID `0x26`, longitud 512 y ausencia de Feature reports | Construir escrituras con la forma correcta |
| Análisis estático de CAM | Buscar nombres, PID, tablas y pistas no visibles en PCAP | Referencias N7 y N9, lógica nativa localizada | Acotar opcodes o transformaciones que las capturas no distinguen |
| Codificación offline | Probar la implementación sin tocar hardware | Encoder compatible con 9 colores, 12 brillos, D22, D24 y D25 | Reutilizarlo en un controlador global con puertas de seguridad |
| Revisión independiente | Intentar refutar hallazgos antes de integrarlos | Correcciones de telemetría, formato HID y documentación | Evitar que una inferencia de un solo análisis se convierta en driver |

## Modelo técnico actual del N9

### Tráfico observado

| Dirección | Prefijo | Interpretación actual |
| --- | --- | --- |
| Salida | `10 02` | Solicitud de información de firmware |
| Entrada | `11 02` | Respuesta de información de firmware |
| Salida | `20 03` | Solicitud de canales o accesorios |
| Entrada | `21 03` | Respuesta de canales o accesorios |
| Entrada | `ff 01` | Confirmación que repite el opcode aceptado |
| Entrada | `ff 03` | Heartbeat periódico, sin telemetría viva |
| Salida | `26 04` | Datos de iluminación observados |
| Salida | `26 06` | Commit o latch de iluminación observado |

### Lo que ya puede afirmarse

- Existe un camino coherente para construir la misma trama que CAM.
- La herramienta actual puede leer sin escribir.
- La herramienta actual puede generar bytes sin abrir el dispositivo.
- Linux ya produjo y revirtió un cambio físico de iluminación fija.
- Linux construyó y aplicó físicamente un color y brillo globales nunca
  capturados de CAM mediante el modelo unificado.
- El protocolo de `Fixed` global está suficientemente cubierto para un
  controlador de color RGB y brillo de 0 a 100. La escritura genérica y la
  interfaz visual todavía no están implementadas.
- La personalización usa la misma trama `26 04` como vector de 49 tripletas
  independientes. CAM transmite el vector completo aunque cambie una sola
  zona.
- El primer rectángulo superior izquierdo es la tripleta 1. El recorrido de
  17 zonas izquierdas, 17 inferiores y 15 derechas está fuertemente respaldado,
  pero todavía no demostrado posición por posición.
- La superficie observada son zonas integradas de la cubierta de la N9. Los
  aros de ventiladores y la RAM no cambiaron durante la prueba.
- No se ha capturado la página Cooling, por lo que no conocemos RPM,
  temperaturas, duty ni curvas del N9.
- No se han decodificado los modos animados.

## Primer hito (cerrado)

Para evitar llamar hito a una demostración frágil, el primer hito se define
como lo siguiente:

> Linux cambia la iluminación fija del N9 con una trama derivada de capturas,
> el cambio físico es observado, la refrigeración permanece estable, el estado
> puede revertirse y la prueba se repite con el mismo resultado.

H1, H2, H3 y H4 quedaron completadas el 21 de julio de 2026. El primer hito
queda alcanzado con un control de iluminación fija reversible, repetible y
acotado en un arnés de laboratorio, no como comando genérico instalable.

### Etapa H1. Preparación y línea base, completada

- Confirmar el dispositivo por `1e71:2023`, no por `/dev/hidrawN` fijo.
- Confirmar que el N9 pertenece a Linux y que CAM no lo controla al mismo
  tiempo.
- Registrar estado visual, temperaturas y giro de ventiladores antes de la
  prueba.
- Validar nuevamente las tramas de rojo y blanco de CAM al 7 por ciento, el
  commit y la recuperación.

**Resultado esperado:** una puerta de seguridad que impida escribir al
dispositivo equivocado o empezar desde un estado térmico anómalo.

### Etapa H2. Primera escritura mínima supervisada, completada

- Enviar únicamente la trama conocida de rojo tenue al 7 por ciento.
- Enviar el commit observado.
- No tocar opcodes de ventiladores, bomba, duty, curvas o firmware.
- Mantener observación física y térmica durante la prueba.

**Resultado esperado:** demostrar que el modelo de escritura observado en CAM
funciona también desde Linux.

### Etapa H3. Observación, mapeo y reversión, completada

- Se registró qué zona de iluminación cambió. Las 49 tripletas no se mapearon
  a LED físicos individuales.
- Se verificaron físicamente los ventiladores, las temperaturas y que todo lo
  demás se percibió normal. El arnés no mide RPM ni bomba, así que no hay
  comprobación instrumentada de la bomba.
- Se aplicó la reversión prevista.
- La reversión por protocolo funcionó. El reinicio completo de la torre sigue
  como recuperación de último recurso ya observada para iluminación.

**Resultado:** se demostró estabilidad térmica, reversibilidad y un cambio
visual acotado, con repetibilidad en el ciclo posterior. No se convierte en
medición de bomba o RPM lo que solo se percibió como normal.

### Etapa H4. Repetición y herramienta mínima, completada

- Se repitió el ciclo rojo y restauración desde el cian restaurado con el mismo
  resultado visual.
- El procedimiento exitoso quedó en `nzxt-n9-first-write-lab`, limitado a
  `Fixed` con tramas congeladas y token de confirmación.
- Existen pruebas offline con digests dorados y límites estrictos, sin acceso a
  hardware real.
- La evidencia documenta N9 Z890, CAM 4.76.5, Canal 6 y brillo 7 por ciento.

**Resultado:** primer control real, reproducible y acotado desde Linux, como
arnés de laboratorio cerrado. En este punto se alcanza el primer hito.

## Objetivo final y seis macroetapas restantes

El objetivo final se define como control útil y mantenible desde Linux de los
componentes objetivo, con seguridad, empaquetado y una ruta upstream. No exige
que cada función viva para siempre en este monorepo. De las siete macroetapas
totales, la primera ya está completa. Quedan seis.

### Macroetapa 1. Iluminación fija del N9, completa

Las cuatro etapas del primer hito están completas en el arnés de laboratorio.
Ampliar color, brillo, canal y mapeo físico es trabajo posterior, sin romper
las puertas de seguridad ya demostradas.

### Macroetapa 2. Iluminación completa del N9

- Identificar canales y superficies físicas.
- Capturar y decodificar efectos animados.
- Determinar si los efectos viven en firmware o si CAM transmite frames
  continuamente.
- Anclar brillo en más de un porcentaje.
- Añadir selección segura de color, brillo y canal.

### Macroetapa 3. Refrigeración del N9

- Capturar la página Cooling con RPM visibles y cambios controlados.
- Encontrar solicitudes y respuestas de telemetría.
- Decodificar RPM, temperaturas y estado de headers.
- Capturar duty fijo y curvas sin aplicar valores no observados.
- Implementar lectura primero, después escritura supervisada y finalmente
  curvas.

Esta es la etapa de mayor riesgo porque el N9 controla todos los headers de
ventiladores de la placa.

### Macroetapa 4. Cooler Master Nex Digital

- Inventariar descriptores y endpoints de `2516:0232`.
- Capturar MasterCTRL por función.
- Separar bomba, ventiladores, ARGB y pantalla.
- Implementar lectura, controles mínimos y después funciones de pantalla.

### Macroetapa 5. Matriz y pantalla del chasis

- Decodificar `ff00:020c`.
- Identificar de forma concluyente `26ce:0a09`.
- Capturar reloj, reloj de arena, sincronización y animaciones.
- Implementar efectos reproducibles sin depender de la suite de Windows.

### Macroetapa 6. Hardware restante

- Completar el soporte del teclado Evision en OpenRGB si sigue faltando.
- Investigar y contribuir el RGB de la Zotac RTX 5060 Ti.
- Añadir otros controladores solo si pertenecen al alcance original o se
  aprueban de forma explícita.

### Macroetapa 7. Producto mantenible y upstream

- Integrar las herramientas estables en `install.sh`, PKGBUILD y paquetes
  Debian.
- Añadir salida JSON y compatibilidad con las herramientas Linux apropiadas.
- Preparar aportes revisables para liquidctl, OpenRGB y liquidtux.
- Probar instalación, actualización, desinstalación y recuperación.
- Publicar versiones con changelog y evidencia de compatibilidad.

## Riesgos y mitigaciones

| Riesgo | Consecuencia posible | Mitigación |
| --- | --- | --- |
| Escribir una trama HID mal formada | Bloqueo del controlador que también maneja ventiladores | Usar solo longitudes y Report ID verificados, comparar contra capturas y empezar con iluminación fija tenue |
| Tocar opcodes de refrigeración antes de entenderlos | Cambio de duty, bomba o curvas | Mantener separados iluminación y Cooling, prohibir opcodes no capturados y exigir supervisión física |
| Escribir al hidraw equivocado | Afectar otro periférico | Resolver siempre por VID, PID, sysfs y descriptor, nunca por número hidraw persistente |
| Dos dueños del USB al mismo tiempo | Estados incoherentes, desconexión o pérdida de capturas | Confirmar si el dispositivo pertenece a Linux o a la VM antes de cada prueba |
| Confundir correlación con causalidad | Implementar campos o fórmulas falsos | Una acción por captura, repeticiones, pruebas discriminantes y etiquetas de evidencia |
| Sobreajustar una fórmula de brillo | Colores incorrectos fuera de los puntos medidos | Marcar extrapolaciones, capturar otro brillo y conservar tramas doradas |
| Asumir que 49 tripletas son 49 LED | Mapeo físico incorrecto | Tratar las 49 entradas como zonas visuales. D27 prueba la primera y todavía se requieren anclas para el resto antes de exponer control completo |
| Pérdida temporal de iluminación | RGB apagado hasta recuperar estado | Mantener trama de reversión, registrar estado previo y usar reinicio completo como recuperación de último recurso ya observada |
| Automatización visual frágil en la VM | Capturas de una superficie equivocada o acciones no verificadas | Verificar la pantalla real, usar rótulos actuales y reservar al humano los gestos visualmente ambiguos |
| Guest Agent desconectado | Imposibilidad de automatizar o inspeccionar Windows | Recuperar el agente antes de una unidad dependiente, usar visor gráfico y no fingir que la VM está operable |
| Filtrar seriales, credenciales o artefactos propietarios | Riesgo de privacidad o licencia | Revisar diffs, excluir secretos y publicar conocimiento del protocolo, no binarios del fabricante |
| Publicar una conclusión prematura upstream | Rechazo del aporte o daño a usuarios | Mantener el borrador privado hasta revisar alcance, mapeo, compatibilidad y pruebas adecuadas antes de upstream |
| Documentación desactualizada | QA equivocado y decisiones basadas en estado viejo | Contrastar documentos descriptivos con código, Git, capturas y hardware antes de cada unidad |

## En qué debemos seguir ahora

El primer hito está cerrado. Ismael decidió el 21 de julio de 2026 completar
por completo la NZXT N9 antes de avanzar al AIO Cooler Master, la matriz del
chasis, la GPU, el teclado u otro hardware. El alcance restante de la placa se
divide en iluminación completa y refrigeración. Ismael decidió completar
primero la iluminación con todo su alcance y abordar refrigeración después.

Hasta entonces, el arnés de iluminación debe seguir siendo de laboratorio:
tramas congeladas, sin parámetros libres y sin empaquetado de sistema. No se
debe ampliar a Cooling, firmware, duty ni curvas sin capturas nuevas y
supervisión física.

La siguiente unidad de iluminación es completar el mapa por zonas con el menor
número de anclas discriminantes. El punto inicial ya está fijado. Conviene
capturar al menos el final de la columna izquierda, los dos extremos del tramo
horizontal y los dos extremos de la columna derecha. Después se debe comprobar
si el modelo global de color y brillo puede reutilizarse o si la ruta por zonas
emplea una cuantización distinta, como sugiere la diferencia `89` frente a
`88` al 25 por ciento. Solo entonces corresponde construir el editor visual de
49 zonas en Linux.

## Artefactos principales

- [Hardware de referencia](HARDWARE.md)
- [Guía de capturas](CAPTURE-GUIDE.md)
- [Evidencia de iluminación del N9](NZXT-N9-CAM-LIGHTING.md)
- [Roadmap normativo](ROADMAP.md)
- [`nzxt-n9` en español](../tools/nzxt-n9/README.es.md)
- [`nzxt-n9` en inglés](../tools/nzxt-n9/README.md)

Los planes de seguridad, capturas, binarios analizados y borradores upstream
que contienen material de trabajo permanecen fuera del repositorio público
hasta que sean apropiados para publicar.
