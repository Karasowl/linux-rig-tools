# linux-rig-tools

**Herramientas Linux para hardware de PC gamer que aún no tiene soporte nativo.**
🇬🇧 [Read in English](README.md)

Las placas base, refrigeraciones líquidas, chasis y periféricos modernos
esconden cada vez más sus curvas de ventiladores, control de bomba, efectos RGB
y pantallas de matriz LED detrás de aplicaciones solo-Windows (NZXT CAM,
Cooler Master MasterCTRL, suites genéricas de chasis). En Linux te quedas con
lo poco que expone la BIOS.

Este monorepo reúne **herramientas pequeñas e independientes** — instala solo
las que tu equipo necesite. Ninguna depende de otra parte del repo.

## Herramientas

| Herramienta | Qué hace | Estado |
|-------------|----------|--------|
| [`rig-diagnose`](tools/rig-diagnose/) | Inventaría tus controladores RGB/ventiladores/refrigeración e informa qué tiene (o no) soporte en Linux. Solo lectura, cero dependencias. | ✅ funciona hoy |
| [`rig-profiles`](tools/rig-profiles/) | Perfiles `quiet` / `balanced` / `performance` para CPU (governor + EPP) y GPU NVIDIA (límite de potencia) sin software del fabricante. | ✅ funciona hoy |
| [`nzxt-n9`](tools/nzxt-n9/) | Curvas de ventiladores, bomba y RGB del controlador embebido en placas NZXT N9 (`1e71:2023`, N9 Z890). Interfaz de laboratorio Fixed por zona disponible. | 🔬 ingeniería inversa |
| [`cm-nex-digital`](tools/cm-nex-digital/) | Bomba, ventiladores, pantalla digital y ARGB del AIO Cooler Master MasterLiquid Core Nex Digital (`2516:0232`). | 🔬 ingeniería inversa |
| [`chassis-ledmatrix`](tools/chassis-ledmatrix/) | Efectos (reloj de arena, reloj, animaciones…) de controladores genéricos de matriz LED de chasis (`ff00:020c` y similares). | 🔬 ingeniería inversa |

Los dispositivos que ya tienen buena casa upstream (OpenRGB, liquidctl) se
**contribuyen upstream, no se duplican** — mira la [hoja de ruta](docs/ROADMAP.md).

## Instalación

Todos los métodos instalan solo las herramientas que elijas.

**Cualquier distro (Arch/CachyOS, Debian/Ubuntu, Fedora, openSUSE…):**

```sh
git clone https://github.com/Karasowl/linux-rig-tools.git
cd linux-rig-tools
sudo ./install.sh            # menú interactivo
sudo ./install.sh --all      # todo lo instalable
sudo ./install.sh --uninstall
```

**Arch / CachyOS / Manjaro** — PKGBUILDs en [`packaging/arch/`](packaging/arch/)
(paquetes AUR planeados cuando aterricen los primeros drivers):

```sh
cd packaging/arch/rig-profiles && makepkg -si
```

**Debian / Ubuntu / Mint / Pop!_OS** — construye paquetes .deb:

```sh
./packaging/debian/build-debs.sh   # genera dist/*.deb
sudo apt install ./dist/rig-profiles_*_all.deb
```

**Fedora / openSUSE** — usa `install.sh` por ahora; COPR/OBS planeados.

## Hardware de referencia

El primer equipo objetivo está documentado por completo en
[docs/HARDWARE.md](docs/HARDWARE.md): NZXT N9 Z890, Intel Core Ultra 7 270K,
Zotac RTX 5060 Ti, Cooler Master MasterLiquid Core Nex Digital, pantalla de
matriz LED del chasis. Si tienes alguno de estos dispositivos, tus
[capturas e informes](docs/CAPTURE-GUIDE.md) son bienvenidísimos.

## Contribuir

Ejecuta `rig-diagnose` y adjunta su salida a tu issue — es lo más útil que
puedes hacer. Para ayudar a decodificar un protocolo, lee la
[guía de capturas](docs/CAPTURE-GUIDE.md). Más en
[CONTRIBUTING.md](CONTRIBUTING.md).

## Licencia

[GPL-3.0-or-later](LICENSE).
