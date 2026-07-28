# nzxt-n9 🔬

Control de ventiladores, header de bomba y RGB para el controlador USB
embebido en las **placas base NZXT N9** (primer objetivo: N9 Z890).

**Estado: ingeniería inversa.** Existen ayudantes de solo lectura y un arnés
cerrado de laboratorio para iluminación. El control de duty de ventiladores,
bomba y una API RGB general todavía no están listos. Este dispositivo es la
razón de que los ventiladores del radiador, el header de bomba y el RGB de la
placa solo puedan configurarse desde la BIOS o desde NZXT CAM en Windows.

## Interfaz de laboratorio Fixed por zona

`bin/nzxt-n9-lab` es una aplicación provisional en PyQt6 para explorar solo
el vector de iluminación `Fixed` respaldado por capturas. Es utilitaria a
propósito, no el diseño final. El módulo de protocolo y modelo está separado
del escritor del dispositivo y de la interfaz, así la interfaz definitiva
podrá sustituir esta superficie sin reescribir el motor.

Desde este checkout del repositorio, ejecuta directamente el laboratorio sin
instalarlo:

```
cd tools/nzxt-n9
./bin/nzxt-n9-lab --offline
```

Requiere Python 3 y PyQt6. En CachyOS o Arch el paquete firmado de repositorio
correspondiente es `python-pyqt6`. Este laboratorio no se conecta a propósito
con `install.sh`, empaquetado ni un servicio del sistema.

El modo offline es obligatorio para desarrollo y QA mecánico. Muestra el
recorrido de 49 zonas, 1-17 por la izquierda, 18-34 por abajo y 35-49 por la
derecha. Permite selección con clic y Ctrl+Clic, RGB hexadecimal o el selector
Qt, brillo para las zonas seleccionadas y un botón explícito **Aplicar**.
Conserva un vector crudo autoritativo de 49 tripletes `GRB`. Aplicar reemplaza
solo los tripletes seleccionados y conserva literalmente los demás, después
envía el vector completo y el commit fijo `26 06`. Offline valida esa
transacción sin abrir hidraw. Registra una **validación offline**, nunca un
envío físico ni un resultado físico de iluminación.

Sin `--offline`, el único destino se resuelve por HID_ID
`0003:00001E71:00002023`. Valida el descriptor de 150 bytes, major:minor del
dispositivo de caracteres antes y después de abrir, vuelve a comprobar HID_ID
y descriptor, y exige un único sensor CPU Package por debajo de 85 C. Antes de
abrir usa `lstat`, exige un dispositivo de caracteres directo, contrasta
major:minor con sysfs y comprueba permiso de escritura. Abre solo ese nodo con
flags de escritura, nonblocking y no-follow, escribe las dos tramas de 512
bytes con 3 ms entre ellas y no reintenta ante ningún error. Un lock en proceso
y un lock advisory no bloqueante por usuario impiden que otro proceso se meta
en la transacción data/commit. La UI ejecuta la extracción D32 y todo I/O en un
worker Qt, y difiere el cierre de ventana hasta acabar la transacción.

El modo real requiere una regla udev con permiso de **escritura** para el nodo
hidraw objetivo. No ejecutes la UI con `sudo` solo para saltar esta comprobación.
Para una sesión de escritorio interactiva, una regla acotada como
`SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1e71", ATTRS{idProduct}=="2023", MODE="0660", TAG+="uaccess"`
es el modelo de permisos previsto. Revisa e instala cualquier regla del sistema
por el flujo normal de administración. No hay controles para payloads, Report
ID, rutas, número de LEDs, Cooling, firmware, ventiladores ni otros opcodes.

`Restaurar D32` lee el PCAP privado D32 en su ruta local fija mediante
`tshark`, extrae de forma de solo lectura la trama final objetivo y exige el
SHA-256 `24a9fd2fbb05769c56505907506c186ba313baa0a277a2506ceb831e77573c70`
antes de enviarla con el commit fijo en modo real. El PCAP no se incluye nunca
en Git. Una ejecución D32 offline se etiqueta solo como validación. Tras una
operación D32 exitosa, su vector crudo exacto pasa a ser la base
preparada. Un Aplicar posterior reemplaza solo sus tripletes seleccionados. La
UI separa estado preparado, último envío físico, validación offline y estado
confirmado físicamente, que queda marcado como desconocido porque los RGB
originales de CAM no se pueden recuperar honestamente del vector crudo.

El candidato por zona se declara como tesis:

```
floor(255 * srgb_encode(srgb_decode(v / 255) * pct / 100) + 0.422545474091919)
```

D26-D32 respaldan escala 255 mediante el valor `89` al 25%. En entradas no
capturadas aún puede diferir por un byte del candidato global anterior de
escala 254. No se presenta como un hecho sobre el algoritmo interno de CAM.

En modo real, antes de que exista una base física autoritativa, el primer
**Aplicar** solo se habilita cuando están seleccionadas las 49 zonas. Un
Aplicar real exitoso o una restauración D32 exitosa establecen ese vector como
base física. Los Aplicar parciales posteriores reemplazan solo los tripletes
seleccionados y preservan literalmente el resto. Offline conserva la
simulación parcial, pero sigue reportando validación y no un envío físico.
Un fallo de escritura de datos o commit invalida la base física porque el
hardware pudo cambiar parcialmente. El siguiente Aplicar real vuelve a exigir
las 49 zonas o una restauración D32 exitosa. Los fallos antes de la primera
escritura no eliminan una base ya conocida.

## Observaciones de iluminación de CAM

Las observaciones manuales de NZXT CAM para una placa N9 Z890, CAM 4.76.5 y
el Canal 6 están documentadas en
[Observaciones de iluminación de NZXT CAM](../../docs/NZXT-N9-CAM-LIGHTING.md).
Son observaciones acotadas a la evidencia, no una garantía universal de
soporte ni una especificación segura de escritura USB.

La evidencia ahora cubre una serie de brillo blanco con doce puntos, nueve
colores al 7% y dos pruebas cruzadas preseleccionadas con colores mixtos. D22
midió `#5A23F4` al 50% como GRB `17 40 b2`. D24 midió `#0E50AD` al 25% como
`27 04 5b`. Ambos coincidieron con predicciones registradas antes de capturar.
El conjunto completo es compatible con un modelo unificado de cuantización,
pero no demuestra el algoritmo interno de CAM ni excluye una tabla de consulta
u otra función que coincida en los puntos medidos.

Con el brillo fijo al 7%, capturas aisladas de color global observaron 49
tripletes repetidos: blanco como `4a 4a 4a`, rojo como `00 4a 00`, azul como
`00 00 4a` y verde como `4a 00 00`.
Bajo la suposición todavía no probada de que estos tripletes codifican
componentes de color, la evidencia favorece el orden de bytes `GRB`. Una
captura de magenta mezclado produjo `00 4a 4a`, lo cual es compatible con que
los componentes rojo y azul estén activos a la vez bajo esa interpretación.
Una captura mezclada no binaria para `#804020` produjo `0c 21 03`. Esto
difiere de una proyección lineal ingenua de componentes y se reprodujo byte
por byte en un segundo frame final. Esto respalda seguir probando una
transformación no lineal, sin identificar una fórmula única ni una tabla de
consulta. Una prueba permutada con `#408020` produjo después el `21 0c 03`
predicho, intercambiando los niveles de los dos primeros componentes y
preservando el tercero. Esto refuerza el orden `GRB` y una transformación
compartida para los niveles medidos. Le siguió `#C08040`, que produjo
`21 36 0c` y agregó el nuevo nivel de componente `36` para la entrada 192. Un
candidato estándar sRGB de luz lineal reproduce las entradas no máximas
observadas 32, 64, 128 y 192 al 7%, pero falla por uno en el componente
completo medido. Una prueba de frontera preseleccionada en la entrada 127
produjo después `20`, lo que refuta un multiplicador exacto de 0.07 y sigue
siendo compatible con un multiplicador efectivo cercano a 0.069 en esa
familia de candidatos. Este es un intervalo de compatibilidad ajustado, no
una fórmula confirmada. Estas capturas no prueban un triplete por LED, no
confirman un índice de canal ni establecen una semántica segura de escritura.

## Modos animados: observaciones decodificadas (D35 a D51)

La serie D35 a D38 (21 y 22 de julio de 2026) aisló `Spectrum Wave` con una
sola acción humana por ventana. La campaña D39 a D46 (22 de julio de 2026)
enumeró después todos los modos de iluminación restantes de CAM y decodificó
los primeros campos, con selecciones en lote atribuibles y capturas dirigidas
de una variable. D47 a D51 (25 y 26 de julio de 2026) cerraron los campos que esa
campaña dejó abiertos. Todo lo siguiente está verificado en los PCAPs
archivados salvo que se etiquete otra cosa, para esta placa, CAM 4.76.5 y el
Canal 6.

**Tres patrones de transporte observados, verificados** (no es una
clasificación completa: `Monitor Temperature` no transmitió nada en su
ventana y su patrón sigue siendo desconocido):

1. **Efectos de firmware** (catorce modos): una trama de configuración
   `2a 04` de 512 bytes por acción del usuario, **sin commit `26 06`** y sin
   más tráfico del host (hasta 174 s de silencio observado mientras la
   animación seguía corriendo). El controlador confirma cada trama con el
   eco `ff 01` del opcode.
2. **Efectos de la familia `26`** (`Marquee`, `Wave`): sin trama `2a`. Cada
   acción envía el vector GRB `26 04` al estilo de `Fixed` más un **commit
   `26 06` parametrizado** 2 a 3 ms después: el byte 4 vale `02` (Fixed usa
   `01`) y el byte 5 selecciona el efecto, `29` Marquee y `35` Wave (`00`
   Fixed). El tamaño de LED de Marquee es el número de tripletas encendidas
   al inicio del vector (un paso de tamaño pasó de 3 a 4). Los demás
   parámetros del commit son **desconocidos**.
3. **Streaming del host** (`Audio Bass`, `Audio Level`): sin trama de
   configuración. CAM emite tramas `26 14` (cabecera `26 14 20 20`, 49
   tripletas) cada 32 ms aproximados, siguiendo el audio, sin commit,
   durante todo el resto de la captura (la salida del modo no se capturó).
   El controlador acusó cada trama cuya ventana de acuse quedó dentro de la
   captura y su heartbeat `ff 03` se detuvo mientras el flujo estuvo activo.

**Identificadores de modo** (byte 4 de `2a 04`), todos medidos en tráfico.
Los modos marcados con * se capturaron en una sola ventana y siguen siendo
observaciones únicas:

| `01` Fading* | `02` Spectrum Wave | `04` Covering Marquee* | `05` Alternating |
|---|---|---|---|
| `06` Pulse* | `07` Breathing | `08` Candle* | `09` Starry Night* |
| `0b` Rainbow Flow* | `0c` Super Rainbow* | `0d` Rainbow Pulse* | `0e` Tai Chi* |
| `0f` Water Cooler* | `10` Loading* | | |

`03` y `0a` no aparecieron nunca. Marquee y Wave no tienen identificador `2a`.

Campos decodificados de `2a 04`, clasificados por evidencia:

- Byte 4, identificador de modo: **verificado** con catorce constantes
  distintas que siguen el orden anunciado de selección en cuatro ventanas
  independientes.
- Bytes 5 y 6, velocidad: **verificado** uint16 little endian (el `Normal`
  de Alternating es 500), menor es más rápido (**verificado** con los
  extremos de Breathing, `Slowest` 40, `Normal` 20 y `Fastest` 4, más la
  aceleración observada en D36). La escala es **por modo y por submodo**,
  así que un valor no significa nada sin ambos. La pista tiene **exactamente
  cinco posiciones** y satura en silencio en **sus dos extremos** (D50 el
  lento, D51 el rápido): una pulsación más no transmite nada. Las dos curvas
  de Alternating están completas y verificadas, de `Fastest` al extremo
  lento: **300/400/500/700/800** con propagación y **600/800/1000/1300/1600**
  sin ella.
- La escala de velocidad es una **tabla, no una función interpolable** (D50),
  y la relación entre submodos **no es un factor constante** (D51). El factor
  2 se cumple exacto en cuatro muescas y se rompe en `Slow` (700 frente a
  1300, razón 1,857). Ninguna tabla se deriva de la otra: la mitad de 1300 es
  650, que es lo que predecía el modelo lineal por tramos para el `Slow` con
  propagación, donde CAM escribe 700. Dentro de un submodo los pasos también
  son irregulares (+100, +100, **+200** y +100 con propagación), lo que
  refutó las candidatas lineal por tramos y geométrica registradas antes de
  D50.
- Ambas ventanas registraron todos los valores antes de capturar. D51 llevaba
  tres controles internos de D48 y los tres se reprodujeron exactos, así que
  el `Slow` discrepante es una medición real. **Una implementación en Linux
  debe transcribir cinco valores crudos por modo y por submodo**, sin
  interpolar y sin derivar entre submodos. Una proyección habría escrito 1400
  donde el valor real es 1300.
- La forma de la escala es por modo: el `Fast` de Alternating es 0,8 veces su
  `Normal` y el de Spectrum Wave 0,6 veces el suyo (150 frente a 250, D36). Los
  extremos de Breathing son 2,0 y 0,2. Alternating es el único efecto que
  expone interruptor de movimiento, así que no hay un segundo modo donde
  contrastar el comportamiento entre submodos. Los demás modos están
  incompletos: Breathing tres muescas de cinco, Spectrum Wave dos de cinco y
  el resto ninguna.
- Bytes 8 en adelante, lista de colores: **verificado** que son entradas
  contiguas de 3 bytes en **orden R B G** (el rojo puro entró como
  `89 00 00` y el azul puro como `00 89 00` al 25 por ciento), el orden
  inverso al G R B de Fixed. El byte 56 es el contador de entradas y al
  eliminar una entrada la lista se compacta. El brillo va **horneado en las
  entradas** (un paso de brillo reescribió solo los bytes de color), con el
  nivel de componente pleno igual al nivel por zona de Fixed al 25 por
  ciento. El cuantizador exacto es **desconocido**.
- Byte 55, campo de bits: el bit 1 es la dirección, **verificado en dos
  modos** (Spectrum Wave de `00` a `02`, Alternating de `01` a `03`). El
  bit 0 es la propagación espacial, **verificado en D47** con el interruptor
  de movimiento de Alternating: con `1` la alternancia recorre la placa, con
  `0` toda la placa conmuta en su sitio. No gobierna la animación, los dos
  colores siguen alternando en ambos estados. Los bits 0 y 1 son
  independientes, **verificado en D48** con los cuatro estados de
  Alternating medidos, y CAM sigue escribiendo el bit 1 con el bit 0
  apagado. Starry Night lleva `01` sin exponer ese interruptor, lo que
  encaja con un modo que siempre se propaga, pero no está verificado.
- Bytes 3, 7 (Candle llevó `56`), 57 y 58 a 59 (`31 03`, pero `31 04` en
  Alternating): significado **desconocido**.

`Monitor Temperature` tiene un **resultado negativo verificado**: elegirlo
junto a su fuente de CPU no transmitió ninguna trama en tres ventanas
separadas, la última en otro día y tras reiniciar por completo la VM (la
placa conservó visiblemente el efecto anterior). El fallo está
en CAM antes de la capa USB, probablemente ligado a las fuentes de
temperatura virtualizadas (**inferencia**). Su patrón de transporte es
**desconocido** y el reintento queda pendiente.

Implicación para Linux, como dirección de ingeniería y no como
especificación: los modos de audio no pueden reproducirse con una escritura
única. Necesitarían un demonio que transmita tramas `26 14` con cadencia de
unos 30 ms. El mismo opcode es una ruta candidata para efectos propios en
tiempo real sobre las 49 zonas renderizados en el host. Nada de esto autoriza
escrituras: ninguna trama `2a 04`, `26 06` parametrizada o `26 14` es todavía
una especificación segura de escritura. Los detalles y la evidencia por
captura están en
[Observaciones de iluminación de NZXT CAM](../../docs/NZXT-N9-CAM-LIGHTING.md).

## Dispositivo

| | |
|---|---|
| USB ID | `1e71:2023` ("NZXT N9 Z890") |
| Interfaz | HID, interfaz única, interrupt IN/OUT |
| Tamaño de paquete | **512 bytes** (wMaxPacketSize 0x0200) |
| App de Windows | NZXT CAM |
| Upstream | ausente de liquidctl (1.15 o anterior) y OpenRGB |

## Lo que sabemos

- Los controladores embebidos previos de NZXT (placas N7, Smart Device V2,
  RGB & Fan Controller `1e71:2009/200e/2010/2011/2019/…`) hablan la familia
  de protocolos Hue 2, bien documentada, con reportes de 64 bytes. liquidctl
  la implementa en `liquidctl/driver/smart_device.py`.
- Los reportes de 512 bytes de este controlador sugieren una **nueva
  generación del protocolo**, pero NZXT suele mantener una estructura de
  comandos similar (escrituras de duty de ventilador estilo `0x60 0x02`,
  escrituras RGB estilo `0x2a`, difusión de estado por interrupt IN).
- La placa no expone **ningún chip Super-I/O hwmon** a Linux: cada header de
  ventilador está detrás de este dispositivo, así que la telemetría de RPM
  también debe salir de aquí.

## Estado de solo lectura (WIP)

Ya existe un primer ayudante de **solo lectura** en `bin/nzxt-n9`. Todavía no
está cableado en los instaladores (`install.sh`, PKGBUILD, debian) porque el
protocolo aún se está decodificando.

```
nzxt-n9 status    # lee unos pocos reportes de entrada 'ff 03' y los decodifica
nzxt-n9 find      # imprime el nodo hidraw de 1e71:2023
```

`status` localiza el nodo `/dev/hidrawN` del controlador por sysfs, lo abre en
**solo lectura** y decodifica el reporte periódico de 512 bytes `ff 03` usando
el mapa de campos de U1:

| offset | significado |
|---|---|
| 0..1 | prefijo `ff 03` (familia heartbeat) |
| 2..13 | eco de 12 bytes del iSerial USB |
| 14..15 | contador de frames `uint16` little-endian (+1 por frame) |
| 16 | flag `0x01` (desconocido, baja confianza) |
| 17..511 | relleno en cero |

Importante: `ff 03` es un **heartbeat o keepalive**. No lleva temperatura viva
de CPU o GPU, ni RPM de ventiladores, ni telemetría de bomba (verificado en
U1). El contador no es un sensor. La telemetría viva parece pedirla el host y
requeriría una *escritura* al dispositivo, que esta herramienta a propósito no
hace.

**Seguridad.** La herramienta nunca escribe al dispositivo: sin reportes HID
de salida, sin reportes de feature, sin `ioctl` que mande datos. La ruta de
lectura usa solo `os.open(..., O_RDONLY | O_NONBLOCK)` de Python más `os.read`
y `os.close`, sin `os.write` ni `fcntl.ioctl`. Una escritura HID mal formada
puede colgar el controlador, así que este ayudante genérico no tiene ruta de
escritura. Las escrituras supervisadas usan el arnés cerrado separado y tramas
congeladas.

Leer `/dev/hidrawN` normalmente necesita permiso. Puedes ejecutar con `sudo` o
agregar una regla udev:

```
# /etc/udev/rules.d/70-nzxt-n9.rules
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1e71", ATTRS{idProduct}=="2023", MODE="0440", TAG+="uaccess"
```

y después `sudo udevadm control --reload && sudo udevadm trigger`.

Requiere `python3` (>=3.10). Sin dependencia de `hidapi`.

## Codificador de tramas (offline, no envía)

`nzxt-n9 encode` construye en memoria la trama de iluminación de 512 bytes del
modo `Fixed` de un color para un color y un brillo, y la imprime en hex. Es una
ayuda de decodificación, una forma de contrastar nuestro modelo contra las
capturas. **Nunca abre `/dev/hidraw` y nunca envía nada.** La primera
escritura física reversible desde Linux usó el arnés de laboratorio cerrado
descrito más abajo, no este codificador genérico.

```
nzxt-n9 encode ff0000 7            # rojo al 7%, imprime la trama de carga en hex
nzxt-n9 encode 804020 7 --commit   # imprime además la trama commit fija '26 06'
nzxt-n9 encode 00ff00 7 --hex-only # solo hex crudo, una trama por línea
```

La estructura de la trama coincide con las escrituras `Fixed` capturadas:

| offset | significado |
|---|---|
| 0 | `0x26` Report ID HID (primer byte del buffer en el cable) |
| 1..3 | `04 20 00` (subcomando `04`, selector de canal `20`, `00`) |
| 4..150 | 49 tripletes idénticos `G R B` (147 bytes) |
| 151..511 | relleno en cero |

Para un componente de entrada `v` y un porcentaje de brillo `p`, el candidato
unificado calcula:

```
floor(254 * srgb_encode(srgb_decode(v / 255) * (p / 100)) + t)
```

La evidencia combinada D1-D24 conserva
`0.4173921478326008 <= t < 0.4276988003512372`. El codificador usa el punto
medio `t = 0.422545474091919`. Reproduce byte por byte los nueve colores
capturados al 7%, los doce puntos capturados de brillo blanco, D22 al 50% y D24
al 25%. La trama commit fija `26 06` también coincide con las capturas. Es un
modelo compatible, no una demostración de la implementación de CAM. Cualquier
combinación de color y brillo no capturada sigue siendo una predicción.

La predicción antes no capturada `#FFD000` al 40%, GRB `89 a9 00`, se aplicó
después desde Linux en la N9 de referencia. Ismael observó un resultado amarillo
o dorado inmediato con ventiladores normales. La trama blanca capturada restauró
el cian habitual y CAM reaplicó su estado recordado al reconectar el USB. Esto
valida físicamente un punto generado fuera del conjunto de capturas. Respalda un
controlador `Fixed` global genérico, pero no cubre personalización por zonas ni
demuestra el algoritmo interno de CAM.

## Arnés de laboratorio de primera escritura (cerrado, no instalado)

`bin/nzxt-n9-first-write-lab` es un **arnés de laboratorio**, no una CLI de
producto y no está cableado en los instaladores. Se usó para la primera
escritura reversible de iluminación desde Linux en la N9 Z890 de referencia
(CAM Fixed, Canal 6, 7%). Ahora acepta cinco superficies:

```
nzxt-n9-first-write-lab preflight
nzxt-n9-first-write-lab apply-red I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab apply-model-yellow40 I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab restore-white I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab --help
```

No hay argumentos de color, brillo, canal, Report ID, ruta hidraw, número de
LED ni payload. Las tramas están congeladas: rojo D12 `#FF0000` al 7%, blanco
CAM D11 `#FFFFFF` al 7% (cian tenue en esta placa), `#FFD000` predicho al 40%
con GRB `89 a9 00` y el commit fijo `26 06` capturado. La trama amarilla era una
predicción no capturada del modelo D1-D24 y su prueba física desde Linux produjo
el amarillo o dorado esperado. Sigue siendo una trama generada por el modelo,
no una medición de CAM. Las escrituras son un par
de reportes exactos de 512 bytes con una pausa de 3 ms. El dispositivo se
resuelve por HID_ID `0003:00001E71:00002023`, descriptor y major:minor, con una
segunda vinculación después de abrir y antes de escribir.

Las pruebas offline viven en `tests/test_nzxt_n9_first_write_lab.py` y
`tests/test_nzxt_n9_encoder.py`. Nunca abren hardware real. No trates este
arnés como una API genérica de iluminación.

## Plan

1. **Capturas** (mira [docs/CAPTURE-GUIDE.md](../../docs/CAPTURE-GUIDE.md)):
   arranque de CAM, cada cambio de duty por canal de ventilador, header de
   bomba, cada modo RGB.
2. Prototipo de solo lectura: decodificar el stream de estado por
   interrupt IN (RPMs, temperaturas).
3. Escrituras de duty de ventilador y RGB, verificadas únicamente contra
   capturas.
4. CLI aquí, y después subir el protocolo upstream a **liquidctl** y un
   driver hwmon de kernel a **liquidtux** para que `sensors` y CoolerControl
   vean los ventiladores.

## Cómo ayudar

¿Tienes una placa N9 (Z890 o más nueva)? Ejecuta `rig-diagnose`, abre un
issue y, si tienes arranque dual: un juego de capturas es un avance enorme.
