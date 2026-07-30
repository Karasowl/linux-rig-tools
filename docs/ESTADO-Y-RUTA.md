# Estado, método y ruta del proyecto

Actualizado: 30 de julio de 2026.

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
Windows reproducible, capturas USB aisladas, la iluminación fija del N9 está
decodificada y validada físicamente, y la decodificación avanzó hasta los
modos animados, con tres laboratorios de escritura cerrados que ya pasaron QA
físico en la placa de referencia.

Herramientas generales seguras:

- `nzxt-n9 status`, que abre el dispositivo en solo lectura y decodifica su
  heartbeat.
- `nzxt-n9 find`, que resuelve el nodo hidraw por identidad HID exacta.
- `nzxt-n9 encode`, que construye tramas en memoria y nunca las transmite.

Superficies de laboratorio, ninguna instalada en el sistema:

- `nzxt-n9-lab`, interfaz PyQt6 del vector Fixed de 49 zonas.
- `nzxt-n9-first-write-lab`, arnés de la primera escritura Fixed.
- `nzxt-n9-animated-write-lab`, arnés de la trama Spectrum Wave D35.
- `nzxt-n9-alternating-write-lab`, arnés de doce tramas Alternating exactas
  de D47, D48, D49, D50 y D51. Son las dos tablas de velocidad completas hacia
  la derecha, cinco muescas cada una, más los dos estados Normal hacia la
  izquierda, con lo que el byte 55 queda cerrado con sus cuatro valores.

Las tres bibliotecas del N9 y sus arneses están cubiertos por 112 pruebas
offline en `tools/nzxt-n9/tests/`.

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

Después del primer hito, Linux también reprodujo físicamente tramas de modos
animados. Estados con QA físico aprobado por el operador:

| Estado | Fecha del QA | Origen |
| --- | --- | --- |
| Spectrum Wave, entrada desde Fixed | 27 de julio de 2026 | D35 |
| Alternating con desplazamiento, Normal | 27 de julio de 2026 | D47 |
| Alternating en posición, Normal | 27 de julio de 2026 | D47 |
| Alternating con desplazamiento, Fastest 300 | 29 de julio de 2026 | D49 |
| Alternating con desplazamiento, Fast 400 | 29 de julio de 2026 | D50 |
| Alternating con desplazamiento, Slow 700 | 29 de julio de 2026 | D50 |
| Alternating con desplazamiento, Slowest 800 | 29 de julio de 2026 | D49 |
| Alternating en posición, Fastest 600 | 29 de julio de 2026 | D51 |
| Alternating en posición, Fast 800 | 29 de julio de 2026 | D51 |
| Alternating en posición, Slow 1300 | 29 de julio de 2026 | D51 |
| Alternating en posición, Slowest 1600 | 29 de julio de 2026 | D51 |
| Alternating con desplazamiento a la izquierda, Normal | 30 de julio de 2026 | D48 |
| Alternating en posición a la izquierda, Normal | 30 de julio de 2026 | D48 |

Todos están publicados en `master`.

Cada uno es una trama capturada completa de 512 bytes, anclada por SHA-256 y
enviada una sola vez, con restauración D32 posterior. No existe encoder de
modos animados ni ninguna especificación de campos apta para escribir.

Las dos filas de D48 no cierran igual sus dos mitades. La inversión del
recorrido se registró de antemano como visible y se vio, así que la dirección
de `03` está corroborada físicamente. El par en el sitio se registró de
antemano como posiblemente indistinguible, porque con la propagación apagada
un cambio de dirección es solo una inversión de fase de una conmutación que no
se desplaza, así que ahí el QA solo establece que `02` se acepta y se
representa con normalidad. Su nombre sigue apoyado en la eliminación dentro del
campo cerrado de dos bits.

Desde el estado actual faltan:

- Seis de las siete macroetapas del objetivo final del proyecto, control útil
  desde Linux de todo el hardware objetivo, con integración, empaquetado y
  aportes a proyectos upstream. La Macroetapa 1, iluminación fija del N9, ya
  está completa, y la Macroetapa 2, iluminación completa del N9, está en curso
  con la enumeración de modos cerrada y la reproducción por trama congelada
  demostrada.

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
- D28 a D32 fijaron los otros límites del recorrido. Los índices 17, 18, 34,
  35 y 49 cambiaron individualmente de `89 89 89` a `00 89 00`, sin alterar
  ninguna otra tripleta.

**Lo que sigue siendo inferencia o desconocido:**

- Las 49 tripletas corresponden a 49 rectángulos controlables de la cubierta,
  pero no prueban que cada rectángulo represente un único LED físico.
- Los seis extremos y cambios de tramo están demostrados. Los rectángulos
  intermedios no se probaron uno por uno. Su numeración se deriva de los conteos
  contiguos de 17, 17 y 15 y de sus extremos anclados.
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
100. La estructura de personalización por zonas está demostrada como un vector
completo de 49 tripletas GRB. El recorrido de 17 zonas izquierdas, 17 inferiores
y 15 derechas tiene todos sus límites anclados. La etapa posterior construyó y
validó una ruta genérica de escritura y una interfaz provisional para probar
ese vector desde Linux.

### 14. Laboratorio visual Fixed completo en Linux

**Hecho verificado el 21 de julio de 2026:** `tools/nzxt-n9/bin/nzxt-n9-lab`
expone las 49 zonas en PyQt6, selección simple y múltiple, color RGB
hexadecimal, brillo entero de 0 a 100, Aplicar explícito y restauración del
vector D32. Es una superficie funcional deliberadamente provisional, no el
diseño final de la aplicación.

El escritor identifica únicamente `0003:00001E71:00002023`, valida descriptor,
dispositivo de caracteres y major:minor antes y después de abrir, exige CPU
Package por debajo de 85 C, serializa la transacción con locks locales y entre
procesos y no reintenta escrituras parciales. La interfaz conserva un vector
crudo autoritativo. El primer Apply físico exige las 49 zonas o D32, y los
Apply parciales posteriores preservan literalmente las zonas no seleccionadas.
Un fallo iniciado después del primer `os.write` invalida esa base.

El checkpoint integrado en `master` pasó 59 pruebas con `ResourceWarning`
tratado como error, compilación Python, arranque Qt offscreen y revisión
independiente. En QA físico, D32 produjo el patrón multicolor esperado,
`#0E50AD` al 25 por ciento produjo azul uniforme de inmediato y una aplicación
posterior de `#FF0000` al 25 por ciento sobre la zona 1 cambió solo esa zona,
conservando azules las otras 48. Ismael realizó además múltiples pruebas de
color, brillo y selección y aceptó Fixed como completo. No se reportaron
anomalías de refrigeración durante esta sesión.

**Conclusión actual:** Fixed global y por zona ya tienen un controlador visual
funcional en Linux. La tesis matemática por zona sigue siendo una inferencia
que puede diferir un nivel de CAM en entradas no capturadas, pero el programa
permite probar directamente esos casos sin volver a construir tramas a mano.
Los efectos animados, Cooling, bomba y ventiladores permanecen fuera de este
hito.

### 15. Serie Spectrum Wave, primera decodificación de un modo animado

**Hechos verificados el 22 de julio de 2026, capturas D35 a D38:**

- Cuatro capturas aisladas con una sola acción humana por ventana: entrar a
  Spectrum Wave desde Fixed, un paso de velocidad de `Normal` a `Fast`, un
  cambio de dirección de derecha a izquierda y una repetición de la entrada
  tras restaurar el estado inicial fuera de captura.
- Cada acción produjo exactamente una escritura interrupt OUT de 512 bytes que
  comienza `2a 04 20 20`. En ninguna de las cuatro ventanas existe una trama
  commit `26 06` ni ninguna otra escritura posterior del host. D35 conservó
  174 segundos de silencio tras la trama y D38 revalidó ese silencio con 75
  segundos.
- El controlador confirmó cada trama con el acuse `ff 01` conocido, que repite
  el opcode `2a 04`, dentro de los 2 ms posteriores a completarse la escritura. El heartbeat
  `ff 03` continuó con su cadencia de 3 segundos y su contador documentado.
- El paso de velocidad cambió únicamente el byte 5, de `fa` (250) a `96`
  (150). El cambio de dirección cambió únicamente el byte 55, de `00` a `02`.
  Los bytes 58 y 59 llevan la constante `31 03` en las cuatro tramas. El resto
  del buffer es cero.
- La trama de D38 es idéntica byte por byte a la de D35, verificado por
  SHA-256 de los payloads extraídos. La transición es reproducible.
- Ismael confirmó físicamente que el arcoíris arrancó, se aceleró de forma
  visible e invirtió su sentido, y que los ventiladores permanecieron normales
  durante toda la serie.

**Inferencias:**

- El byte 4 `02` como identificador del modo Spectrum Wave. Falta capturar un
  segundo modo animado para discriminarlo.
- Menor valor de velocidad es más rápido, con solo dos puntos medidos.
- La familia `2a 04` como escritura de configuración de efectos animados,
  distinta del `26 04` de Fixed.

**Desconocido:**

- El ancho del campo de velocidad, 1 o 2 bytes, porque el byte 6 fue `00` en
  ambos estados. Los valores de `Slowest`, `Slow` y `Fastest` no están
  capturados.
- El significado de `31 03` y del byte 3 `20`, que en Fixed es `00`.

**Conclusión:** para Spectrum Wave en esta placa, CAM envía una única trama de
configuración por acción y la animación vive en el firmware del controlador.
CAM no transmite frames de animación y no usó commit en ninguna de las cuatro
capturas de este modo. Extender esa ausencia de commit a otros modos que usen
`2a 04` sigue siendo una inferencia hasta capturarlos. Los
detalles verificados y la clasificación de cada campo están en
[NZXT-N9-CAM-LIGHTING.md](NZXT-N9-CAM-LIGHTING.md) y en los archivos
D35-ANALYSIS.md a D38-ANALYSIS.md junto a las capturas privadas.

### 16. Campaña de modos animados, enumeración y campos (D39 a D46)

**Hechos verificados el 22 de julio de 2026, capturas D39 a D46:**

**Metodología por lotes.** Para enumerar rápido sin perder atribución, D39 a
D42 capturaron selecciones en lote: el operador eligió los modos anunciados en
orden, con pausas mayores de 12 segundos y sin tocar ningún otro control, y
cada escritura se atribuye por orden anunciado y timestamp. D43 a D45 fueron
capturas dirigidas de una variable (lista de colores, tamaño y dirección,
brillo y extremos de velocidad). D46 fue exploratoria con resultado negativo.
El trabajador de decodificación reverificó cada afirmación contra los PCAPs
archivados, con SHA-256 cotejado contra los sidecars.

**Resultados verificados:**

- Los modos capturados usaron tres patrones de transporte: la trama única
  `2a 04` sin commit para catorce modos renderizados en firmware, el par
  `26 04` más `26 06` parametrizado para Marquee y Wave, y el streaming
  `26 14` renderizado en el host para los modos de audio. No es una
  clasificación completa: el patrón de Temperature Monitor sigue siendo
  desconocido porque no transmitió nada.
- El byte 4 de la trama `2a 04` es el identificador de modo, ya verificado
  con catorce constantes distintas: Fading `01`, Spectrum Wave `02`,
  Covering Marquee `04`, Alternating `05`, Pulse `06`, Breathing `07`,
  Candle `08`, Starry Night `09`, Rainbow Flow `0b`, Super Rainbow `0c`,
  Rainbow Pulse `0d`, Tai Chi `0e`, Water Cooler `0f` y Loading `10`. Los
  valores `03` y `0a` no aparecieron nunca.
- La velocidad es un uint16 little endian en los bytes 5 y 6, demostrado por
  el Normal de Alternating con valor 500. Menor es más rápido, con los
  extremos de Breathing medidos: Slowest 40, Normal 20 y Fastest 4. La
  escala es por modo y además por submodo, así que la misma muesca de la
  interfaz se traduce a valores crudos distintos según el bit 0 del byte 55,
  y eso explica el 1000 que D47 dejó sin resolver. La pista tiene
  exactamente cinco posiciones y satura en silencio en sus dos extremos,
  verificado en D50 (extremo lento) y D51 (extremo rápido): una pulsación
  más no transmite nada, con 48 y 31,8 segundos de cola que descartan una
  escritura tardía. Las dos curvas de Alternating están completas y
  verificadas: con propagación 300, 400, 500, 700 y 800, y sin propagación
  600, 800, 1000, 1300 y 1600, de Fastest al extremo lento.
- La escala de velocidad es una tabla, no una función interpolable
  (verificado en D50), y la relación entre submodos no es un factor
  constante (verificado en D51). El factor 2 se cumple exacto en cuatro
  muescas y se rompe en Slow, donde 700 y 1300 dan 1,857. Ninguna de las dos
  tablas se deriva limpiamente de la otra: la mitad de 1300 es 650, que es
  lo que predecía el modelo lineal por tramos para el Slow con propagación,
  donde CAM escribe 700. Son dos tablas independientes que coinciden en un
  factor 2 en cuatro puntos por razones desconocidas.
- Dentro de un submodo los pasos también son irregulares: +100, +100, +200 y
  +100 con propagación. Eso refutó las dos fórmulas candidatas registradas
  antes de D50, la lineal por tramos que predecía Slow 650 y la geométrica
  por mitades que predecía 632. El modelo lineal en todo el rango y el
  geométrico de razón constante ya estaban excluidos por el Normal medido.
- Consecuencia práctica para Linux: la velocidad no es interpolable dentro
  de un submodo ni derivable entre submodos. Cada par de modo y submodo
  exige transcribir sus cinco valores crudos medidos. Una proyección habría
  escrito 1400 donde el valor real es 1300.
- La forma de la escala es por modo: el Fast de Alternating es 0,8 veces su
  Normal y el de Spectrum Wave 0,6 veces el suyo (150 frente a 250, D36). Los
  extremos de Breathing son 2,0 y 0,2. Las dos curvas de Alternating
  difieren en forma solo en Slow, 1,4 frente a 1,3.
- La lista de colores empieza en el byte 8 con tripletas contiguas en orden
  R B G, ancladas en D43 con rojo puro `89 00 00` y azul puro `00 89 00` al
  25 por ciento. Es el orden inverso al G R B de Fixed. El byte 56 es el
  contador de entradas y al eliminar una entrada la lista se compacta.
- El brillo de los modos animados se hornea en las tripletas de la lista.
  Un punto porcentual movió `27 3e 00` a `28 40 00` y `00 89 00` a
  `00 8b 00` sin tocar ningún otro byte.
- El byte 55 es un campo de bits. El bit 1 es la dirección, verificado en
  dos modos (Spectrum Wave `00` a `02`, Alternating `01` a `03`). El bit 0
  es la propagación espacial, verificado en D47 con el interruptor de
  movimiento de Alternating: con `1` la alternancia recorre la placa, con
  `0` toda la placa conmuta en su sitio. No gobierna la animación, porque
  los dos colores siguen alternando en ambos estados. Los dos bits son
  independientes y ortogonales, verificado en D48 con los cuatro estados de
  Alternating medidos (`00`, `01`, `02` y `03`). CAM sigue escribiendo el
  bit 1 con el bit 0 apagado, así que la dirección nunca deja de emitirse. Sin
  propagación su efecto visible se reduce a invertir la fase. Starry
  Night lleva `01` sin exponer ese interruptor, lo que encaja con un modo
  que siempre se propaga, pero no está verificado.
- Marquee y Wave no usan la familia `2a`. Envían el vector `26 04` más un
  `26 06` parametrizado: byte 4 `02` y selector de efecto en el byte 5,
  `29` Marquee y `35` Wave, frente al `01 00` del commit constante de
  Fixed. El tamaño de LED de Marquee es el número de tripletas encendidas
  al inicio del vector, verificado con un paso de 3 a 4.
- Los modos Audio Bass y Audio Level no envían configuración. CAM emite un
  flujo continuo de tramas `26 14` de 49 tripletas cada 32 ms
  aproximadamente, sin commit, que sigue el audio. El controlador acusó con
  `ff 01` cada trama cuya ventana de acuse quedó dentro de la captura, 2175
  acuses para 2176 escrituras, y su heartbeat `ff 03` se detuvo mientras el flujo
  estuvo activo. El efecto vive en el host.
- Temperature Monitor tiene resultado negativo verificado por partida
  doble: cero escrituras en su tramo de D42 y cero escrituras en toda la
  ventana dedicada D46, pese a los intentos del operador. El fallo ocurre
  en CAM antes del USB. Causa desconocida, con la hipótesis de las fuentes
  de temperatura virtualizadas de la VM.
- Reproducibilidad entre ventanas: cuatro tramas resultaron idénticas byte
  por byte entre capturas independientes (Breathing en D39 y D43, el estado
  de dos colores de Breathing entre D43 y D45, Alternating en D41 y D44 y
  el vector de Marquee en D39 y D44), verificado por SHA-256 de los
  volcados.

**Desconocido:** el significado de los bytes 3, 7 (Candle llevó `56`), 57 y
58 a 59 (`31 03`, con `31 04` en Alternating), los parámetros restantes del
`26 06` parametrizado, el orden de componentes de las tripletas `26 14`, los
rangos de velocidad de los modos distintos de Breathing y el máximo real de
la lista de colores. Ningún campo de `2a 04`, `26 06` parametrizado o
`26 14` es todavía una especificación segura de escritura.

Los detalles por captura están en los archivos D39-ANALYSIS.md a
D46-ANALYSIS.md junto a las capturas privadas, y el mapa consolidado de
campos está en [NZXT-N9-CAM-LIGHTING.md](NZXT-N9-CAM-LIGHTING.md).

### 17. Laboratorios de escritura de modos animados y su QA físico

**Hechos verificados entre el 27 y el 29 de julio de 2026.**

La decodificación de los modos animados dejó claro que sus campos todavía no
son una especificación segura. Para poder demostrar control físico sin
inventar bytes se adoptó un patrón distinto del encoder de Fixed: congelar la
trama capturada completa y exponerla como una operación con nombre.

**Regla del patrón.** Cada operación de un laboratorio de escritura envía un
payload de 512 bytes extraído de una PCAP privada y anclado por su SHA-256.
No hay encoder, interpolación, parámetro libre ni síntesis por campos. La
operación no acepta color, brillo, velocidad numérica, dirección, canal ni
ruta hidraw. Aplicar realiza una única escritura, sin reintento, sin pausa y
sin segunda escritura, bajo el mismo lock exclusivo que Fixed. Toda operación
va acompañada de la restauración exacta D32.

**Artefactos:**

- `nzxt-n9-animated-write-lab`, una sola operación con la trama D35 de entrada
  a Spectrum Wave.
- `nzxt-n9-alternating-write-lab`, seis operaciones con tramas exactas de D47,
  D49 y D50: las cinco velocidades con desplazamiento hacia la derecha y el
  estado en posición Normal.

**Método de cada unidad.** Implementación en un worktree aislado sobre el
commit publicado, revisión independiente por otro modelo con permiso para
reextraer las PCAP y ejecutar la suite, y solo después un ciclo físico
autorizado explícitamente por Ismael, con observación humana de iluminación,
bomba y ventiladores, y restauración D32 entre estados.

**Resultado.** Los siete estados de la tabla del resumen ejecutivo se
comportaron como se esperaba. Las cuatro velocidades nuevas se vieron como
velocidades claramente distintas del mismo efecto, en el orden previsto. En
ningún ciclo se observó anomalía de refrigeración, las temperaturas se
mantuvieron muy por debajo de la puerta de 85 grados Celsius y el nodo hidraw
quedó siempre libre al terminar.

**Límite importante.** Este QA valida esas tramas exactas en esta placa. No
valida los campos que las componen, no autoriza estados no medidos y no
convierte la velocidad en un parámetro. La escala de velocidad es una tabla
medida y no una función, verificado en D50 y D51, así que cada muesca nueva
exige su propia captura.

**Nota operativa verificada el 29 de julio de 2026:** entre sesiones el N9
cambió de `/dev/hidraw2` a `/dev/hidraw3`. Ningún laboratorio se vio afectado
porque todos resuelven el nodo por identidad HID exacta. Las menciones a un
número de hidraw concreto en la documentación son registros históricos de
cada sesión, no configuración.

## Técnicas usadas y qué esperamos obtener de cada una

| Técnica | Para qué se usa | Qué ha producido | Qué esperamos obtener después |
| --- | --- | --- | --- |
| Inventario con sysfs, `lsusb`, hidraw y sensores | Identificar el hardware real y sus límites | VID, PID, interfaces y ausencia de PWM Linux | Detección estable sin depender de números de bus o hidraw |
| QEMU/KVM y passthrough USB | Ejecutar las aplicaciones oficiales contra el hardware real | Laboratorio Windows reproducible | Capturar Cooling, efectos y dispositivos restantes |
| `usbmon`, tshark y PCAP | Observar bytes sin escribir desde Linux | Handshake, heartbeat y tramas de iluminación | Descubrir telemetría, canales, efectos y controles |
| Experimentos diferenciales | Relacionar una acción con una diferencia de tráfico | Series D1 a D51 con acciones aisladas o lotes atribuibles | Reducir falsos positivos y establecer causalidad más fuerte |
| Repetición byte por byte | Separar coincidencias de comportamiento reproducible | Repetición de brillo y colores mixtos | Tramas doradas para pruebas automáticas |
| Pruebas discriminantes | Refutar fórmulas que coinciden por accidente | El modelo sobrevivió D22, D24 y una escritura física inédita D25. D26 a D32 aislaron estado y límites por zona | Usar el laboratorio Fixed para detectar cruces que difieran de la tesis por zona |
| Análisis del descriptor HID | Resolver formato y dirección de reportes | Report ID `0x26`, longitud 512 y ausencia de Feature reports | Construir escrituras con la forma correcta |
| Análisis estático de CAM | Buscar nombres, PID, tablas y pistas no visibles en PCAP | Referencias N7 y N9, lógica nativa localizada | Acotar opcodes o transformaciones que las capturas no distinguen |
| Codificación offline | Probar la implementación sin tocar hardware | Encoder compatible con 9 colores, 12 brillos, D22, D24 y D25, más los tres laboratorios del N9 cubiertos por 104 pruebas | Extender el mismo enfoque a cada modo siguiente |
| Trama congelada por SHA-256 | Demostrar control físico de un modo cuyos campos aún no son especificación | Siete estados animados reproducidos y revertidos, sin encoder ni parámetros | Aplicarlo a cada tabla nueva hasta que los campos estén demostrados |
| Revisión independiente | Intentar refutar hallazgos antes de integrarlos | Correcciones de telemetría, formato HID, concurrencia, estado físico y documentación, y una puerta obligatoria por unidad antes del QA físico | Evitar que una inferencia de un solo análisis se convierta en driver |

## Modelo técnico actual del N9

### Tráfico observado

| Dirección | Prefijo | Interpretación actual |
| --- | --- | --- |
| Salida | `10 02` | Solicitud de información de firmware |
| Entrada | `11 02` | Respuesta de información de firmware |
| Salida | `20 03` | Solicitud de canales o accesorios |
| Entrada | `21 03` | Respuesta de canales o accesorios |
| Entrada | `ff 01` | Confirmación que repite el opcode aceptado, observada tras `20 03`, `26 04`, `26 06`, `2a 04` y cada `26 14` del streaming |
| Entrada | `ff 03` | Heartbeat periódico, sin telemetría viva. Se detuvo durante el streaming `26 14` de D42 |
| Salida | `26 04` | Datos de iluminación observados, vector de Fixed y también de Marquee y Wave |
| Salida | `26 06` | Commit o latch de iluminación observado. Constante en Fixed y parametrizado en bytes 4 y 5 para Marquee y Wave |
| Salida | `2a 04` | Configuración de efecto animado, una trama por acción y sin commit, observada en catorce modos de firmware |
| Salida | `26 14` | Trama de streaming en tiempo real de 49 tripletas, cada 32 ms aproximados y sin commit, observada en los modos de audio |

### Lo que ya puede afirmarse

- Existe un camino coherente para construir la misma trama que CAM.
- La herramienta actual puede leer sin escribir.
- La herramienta puede generar y validar bytes sin abrir el dispositivo en
  modo offline.
- Linux ya produjo y revirtió un cambio físico de iluminación fija.
- Linux construyó y aplicó físicamente un color y brillo globales nunca
  capturados de CAM mediante el modelo unificado.
- El protocolo de `Fixed` global y por zona está cubierto por un controlador
  visual provisional con color RGB, brillo de 0 a 100 y selección de 49 zonas.
- La personalización usa la misma trama `26 04` como vector de 49 tripletas
  independientes. CAM transmite el vector completo aunque cambie una sola
  zona.
- Los límites 1, 17, 18, 34, 35 y 49 están demostrados mediante cambios
  diferenciales. El recorrido resultante es 17 zonas izquierdas de arriba a
  abajo, 17 inferiores de izquierda a derecha y 15 derechas de arriba a abajo.
- Los rectángulos intermedios siguen el recorrido contiguo contado en CAM, pero
  no recibieron 43 capturas individuales.
- La superficie observada son zonas integradas de la cubierta de la N9. Los
  aros de ventiladores y la RAM no cambiaron durante la prueba.
- No se ha capturado la página Cooling, por lo que no conocemos RPM,
  temperaturas, duty ni curvas del N9.
- Los modos animados están enumerados por completo. Catorce modos usan la
  trama `2a 04` con identificador en el byte 4, velocidad uint16 con escala
  por modo, lista de colores R B G con brillo horneado y campo de bits en el
  byte 55. Marquee y Wave usan el par `26 04` más `26 06` parametrizado. Los
  modos de audio son streaming `26 14` del host a unos 32 ms por trama.
  Temperature Monitor no llegó a transmitir en la VM. Ningún campo de
  `2a 04`, `26 06` parametrizado o `26 14` es todavía una especificación
  segura de escritura.
- Linux ya reprodujo físicamente siete estados de modos animados enviando la
  trama `2a 04` capturada completa y anclada por SHA-256, con restauración
  D32 posterior. Eso demuestra que la familia `2a 04` se puede escribir desde
  Linux sin commit y sin efectos colaterales observados, pero no valida
  ninguno de sus campos por separado. La distinción es la que separa
  reproducir una medición de tener una especificación.

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

### Macroetapa 2. Iluminación completa del N9, en curso

- Capturar y decodificar efectos animados. **Hecho en su enumeración:** los
  catorce modos de firmware, Marquee, Wave y los dos modos de audio están
  identificados, y los campos principales de `2a 04` están clasificados.
- Determinar si los efectos viven en firmware o si CAM transmite frames
  continuamente. **Hecho:** catorce modos viven en firmware con una sola
  trama por acción, y solo los modos de audio son streaming del host.
- Anclar brillo en más de un porcentaje. **Hecho:** el brillo de los modos
  animados va horneado en las tripletas de la lista de colores, anclado con
  cambios de un punto porcentual.
- Demostrar escritura física de modos animados. **Hecho por trama congelada:**
  siete estados reproducidos y revertidos, sin encoder.
- Identificar canales y superficies físicas. **Pendiente.**
- Completar las tablas de velocidad medidas por modo y submodo.
  **Pendiente:** solo Alternating tiene sus dos curvas completas.
- Resolver los bytes sin semántica de `2a 04` (3, 7, 57 y 58 a 59) y los
  parámetros restantes del `26 06` parametrizado. **Pendiente.**
- Añadir selección segura de color, brillo y canal para modos animados.
  **Pendiente y bloqueado** hasta que los campos dejen de ser inferencias.

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
| Asumir que 49 tripletas son 49 LED | Mapeo físico incorrecto | Tratar las 49 entradas como zonas visuales. D27 a D32 anclan los límites, pero no demuestran un LED eléctrico por rectángulo |
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

La regla sobre los modos animados es más precisa desde los laboratorios de
escritura, así que conviene enunciarla sin ambigüedad. Está permitido enviar
una trama `2a 04` capturada completa, anclada por SHA-256 y expuesta como
operación con nombre, siempre bajo autorización explícita y con restauración
D32 disponible. Está prohibido construir una trama a partir de sus campos,
interpolar una velocidad, derivar una tabla de otra o exponer un parámetro
libre. Ningún campo de `2a 04`, del `26 06` parametrizado o del `26 14` es
todavía una especificación de escritura, y el `26 14` de los modos de audio no
se ha reproducido nunca desde Linux.

Fixed quedó aceptado como completo tras el QA físico del laboratorio visual.
La serie D35 a D38 abrió la decodificación de los modos animados con Spectrum
Wave y la campaña D39 a D46 completó la enumeración de modos y los primeros
campos: identificador de modo verificado, velocidad uint16 con escala por
modo, lista de colores R B G con brillo horneado, bit de dirección, la
familia `26 06` parametrizada de Marquee y Wave y el streaming `26 14` de los
modos de audio. D47 a D51 cerraron las dos curvas de velocidad de Alternating
y demostraron que la escala es una tabla y no una función.

Entre el 27 y el 30 de julio de 2026 la decodificación pasó a demostración
física por trama congelada. Ya tienen QA físico aprobado Spectrum Wave D35,
los dos Normal de Alternating de D47, las cinco velocidades con desplazamiento
de D49 y D50, las cuatro muescas en el sitio de D51 y los dos Normal hacia la
izquierda de D48, todos publicados en `master`.

Con eso Alternating queda cerrado en todos los estados que existe en alguna
captura. Sus dos tablas de velocidad están completas y sus cuatro valores de
dirección y propagación se han escrito en la placa. Lo que falta de ese modo
no está medido en ninguna parte, empezando por cualquier velocidad hacia la
izquierda distinta de Normal, y no se puede inferir.

Los pendientes concretos de iluminación, en orden natural:

- Reintentar Temperature Monitor, quizá tras reiniciar CAM o con otra fuente
  de temperatura, para determinar su patrón de transporte. Hoy tiene triple
  resultado negativo en la VM (D42, D46 y D47) y ninguna trama capturada.
- Medir las cinco muescas de los modos distintos de Alternating. Hoy
  Breathing tiene tres de cinco y Spectrum Wave dos de cinco, y el resto
  ninguna. Tras D51 no cabe proyectarlas: hay que medirlas una a una.
- Investigar la causa de la desviación de Slow entre submodos. Es compatible
  con un redondeo de un periodo interno, con dos tablas escritas a mano en
  CAM o con otra unidad en ese tramo. Nada de eso está probado.
- Medir las escalas de velocidad de los modos distintos de Breathing y
  Alternating. Son la mayoría y admiten una ventana en lote.

Aparcado a propósito hasta terminar la decodificación, decidido el 25 de
julio de 2026: la limpieza de los PCAP históricos grandes. `usbmon` captura
el bus completo, así que D5 (271 MB), D6 (165 y 46 MB) y D42 (63 MB) llevan
sobre todo tráfico de otros dispositivos. Existe
`captures/nzxt-n9/filter-capture.sh`, que deriva el tráfico del dispositivo
leyendo bus y device del sidecar de cada ventana, con dos guardas (al menos
una escritura y volcado idéntico byte a byte) y sin borrar nunca. La poda es
un comando aparte, bloqueado tras una verificación independiente. Cuando se
retome, el dictamen sobre qué ventana admite poda debe ser externo: D5, D6 y
`linux-passive` son exploración temprana cuyo objeto de estudio pudo ser el
bus mismo, así que filtrarlas por dispositivo no es equivalente a filtrar una
ventana de modos. D48 ya se podó el 25 de julio, con equivalencia verificada
byte a byte y el hash del crudo conservado en su sidecar, pero sin esa
verificación independiente.

El factor 2 entre submodos no admite contraste en otro modo: Alternating es
el único efecto de la matriz que expone interruptor de movimiento, así que
está medido en el único sitio donde ese submodo existe.
- Capturar los extremos de velocidad de los modos distintos de Breathing,
  que fijan el rango por modo del campo uint16.
- Discriminar los parámetros restantes del `26 06` parametrizado y los bytes
  aún sin semántica de la trama `2a 04` (3, 7, 57 y 58 a 59).

Con la iluminación cerrada, sigue la Macroetapa 3, refrigeración del N9:
capturar la página Cooling con RPM visibles, encontrar la telemetría real de
temperaturas y ventiladores, y decodificar duty y curvas con lectura primero
y escritura supervisada después. Es la etapa de mayor riesgo porque el N9
controla todos los headers de ventiladores de la placa.

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
