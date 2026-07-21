# nzxt-n9 🔬

Control de ventiladores, header de bomba y RGB para el controlador USB
embebido en las **placas base NZXT N9** (primer objetivo: N9 Z890).

**Estado: ingeniería inversa.** Existen ayudantes de solo lectura y un arnés
cerrado de laboratorio para iluminación. El control de duty de ventiladores,
bomba y una API RGB general todavía no están listos. Este dispositivo es la
razón de que los ventiladores del radiador, el header de bomba y el RGB de la
placa solo puedan configurarse desde la BIOS o desde NZXT CAM en Windows.

## Observaciones de iluminación de CAM

Las observaciones manuales de NZXT CAM para una placa N9 Z890, CAM 4.76.5 y
el Canal 6 están documentadas en
[Observaciones de iluminación de NZXT CAM](../../docs/NZXT-N9-CAM-LIGHTING.md).
Son observaciones acotadas a la evidencia, no una garantía universal de
soporte ni una especificación segura de escritura USB.

La evidencia actual de brillo, con doce puntos, rechaza una hipótesis exacta
de redondeo sRGB tanto al 2% como al 7%. El resultado al 7% respalda una
familia de cuantizadores compatible ajustada, pero no identifica una fórmula
única ni prueba una tabla de consulta arbitraria. Esto no establece una
implementación en Linux, un protocolo completo ni permiso para reproducir las
cargas USB observadas.

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
puede colgar el controlador, así que la escritura queda fuera hasta probar el
protocolo con capturas.

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

Cada byte de componente es `round_half_up(254 * srgb_encode(srgb_decode(v/255) * k))`
con una constante de brillo `k`. Al 7% `k` cae en el intervalo ajustado
`[0.069272, 0.069968]`; el codificador usa un valor representativo que reproduce
cada byte medido al 7%. La salida se validó **byte por byte al 7%** contra nueve
capturas reales (blanco, rojo, azul, verde, magenta, `#804020`, `#408020`,
`#C08040`, `#7F7F7F`), y la trama commit fija `26 06` coincide en las nueve.

**Solo el 7% está validado con capturas.** Para cualquier otro brillo el
codificador escala `k` linealmente desde el ancla del 7%. Ese `k(b)` es un
modelo, no anclado punto por punto, así que un byte predicho puede diferir de
CAM en un nivel a ciertos brillos. Trata la salida fuera del 7% como una
hipótesis, no como una medición.

## Arnés de laboratorio de primera escritura (cerrado, no instalado)

`bin/nzxt-n9-first-write-lab` es un **arnés de laboratorio**, no una CLI de
producto y no está cableado en los instaladores. Se usó para la primera
escritura reversible de iluminación desde Linux en la N9 Z890 de referencia
(CAM Fixed, Canal 6, 7%). Solo acepta cuatro superficies:

```
nzxt-n9-first-write-lab preflight
nzxt-n9-first-write-lab apply-red I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab restore-white I-CONFIRM-1E71:2023-LIGHTING-ONLY-WRITE
nzxt-n9-first-write-lab --help
```

No hay argumentos de color, brillo, canal, Report ID, ruta hidraw, número de
LED ni payload. Las tramas están congeladas: rojo D12 `#FF0000` al 7%, blanco
CAM D11 `#FFFFFF` al 7% (cian tenue en esta placa) y el commit fijo `26 06`.
Las escrituras son un par de reportes exactos de 512 bytes con una pausa de
3 ms. El dispositivo se resuelve por HID_ID `0003:00001E71:00002023`,
descriptor y major:minor, con una segunda vinculación después de abrir y
antes de escribir.

Las pruebas offline viven en `tests/test_nzxt_n9_first_write_lab.py` y nunca
abren hardware real. No trates este arnés como una API genérica de
iluminación.

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
