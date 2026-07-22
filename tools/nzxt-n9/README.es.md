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
transacción sin abrir hidraw.

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
antes de enviarla con el commit fijo. El PCAP no se incluye nunca en Git. Tras
una restauración D32 exitosa, su vector crudo exacto pasa a ser la base
preparada. Un Aplicar posterior reemplaza solo sus tripletes seleccionados. La
UI separa estado preparado, último envío exitoso y estado confirmado
físicamente, que queda marcado como desconocido porque los RGB originales de
CAM no se pueden recuperar honestamente del vector crudo.

El candidato por zona se declara como tesis:

```
floor(255 * srgb_encode(srgb_decode(v / 255) * pct / 100) + 0.422545474091919)
```

D26-D32 respaldan escala 255 mediante el valor `89` al 25%. En entradas no
capturadas aún puede diferir por un byte del candidato global anterior de
escala 254. No se presenta como un hecho sobre el algoritmo interno de CAM.

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
