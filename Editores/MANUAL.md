# Manual de los editores de hitbox — Alcalde Digital

Esta guía es para alguien que va a crear hitboxes (cajas de colisión) para el
juego y no ha tocado estas herramientas antes. No necesitas saber programar
para usarlas, solo seguir los pasos.

> Estos editores vienen del proyecto EmpatiaQuest y son bastante completos:
> tienen funciones que aquí no usamos (NPCs, objetos de decoración, pupitres).
> Al final hay una sección con lo que puedes ignorar tranquilamente.

## ¿Qué es un hitbox?

Es la caja invisible que usa el juego para saber "aquí hay una pared" o "aquí
el jugador puede interactuar". No es lo que se ve en pantalla (la imagen), es
la zona de colisión que hay detrás de esa imagen.

Hay dos editores que sí nos sirven:

- **`hitbox_editor.py`**: marca paredes y zonas interactuables sobre el fondo
  de un escenario (por ejemplo la ciudad).
- **`personaje_editor.py`**: ajusta los hitboxes de un personaje sobre su
  sprite — uno rojo (con qué choca) y uno amarillo (dónde se puede
  interactuar con él).

## 1. Requisitos antes de empezar

Necesitas Python y la librería `pygame`. Para revisar si ya la tienes, abre
una terminal (PowerShell) y escribe:

```
pip install pygame
```

Si dice "Requirement already satisfied", ya la tienes.

**Ojo:** si tienes más de un Python instalado (común con VS Code o Anaconda),
instala pygame en el MISMO Python con el que vas a correr los scripts. Si al
abrir un editor sale `ModuleNotFoundError: No module named 'pygame'`, es eso.
Se arregla corriendo, con el mismo ejecutable con el que corres el script:

```
<ruta_a_tu_python.exe> -m pip install pygame
```

## 2. Ubícate en la carpeta correcta

Abre una terminal y entra a la carpeta del proyecto (`Estructuras_Datos`), la
misma donde está `main.py`. Todos los comandos se corren desde ahí.

## 3. Editor de escenario (paredes y zonas interactuables)

### Antes de correrlo

Pon la imagen de fondo dentro de `Imagenes/Fondos/`.

### Cómo correrlo

```
python Editores/hitbox_editor.py
```

Se abre primero un selector visual con las imágenes de `Imagenes/Fondos/`;
eliges una con doble clic o Enter. También puedes saltarte el selector
pasando la imagen directo:

```
python Editores/hitbox_editor.py Imagenes/Fondos/fondo_ciudad.png
```

El editor abre en pantalla completa sin bordes. Para salir siempre: `ESC`.

### Controles que vas a usar de verdad

**Crear y borrar cajas**

| Tecla / acción | Qué hace |
| --- | --- |
| Click izquierdo + arrastrar | Dibuja una caja nueva |
| Click derecho sobre una caja | La borra |
| `M` | Activa/desactiva el modo mover: con él activo, arrastrar una caja la mueve en vez de crear una nueva |
| `C` (sin Ctrl) | Borra TODAS las cajas — cuidado, no pregunta |

**Tipo de caja**

| Tecla | Qué hace |
| --- | --- |
| `I` | Cambia entre pared (`wall`) y zona interactuable (`interactable`) |
| `F` | Cambia la forma: rectángulo → círculo → línea |
| `+` / `-` | Grosor de la línea (solo cuando la forma es línea) |

**Moverte por la imagen**

| Tecla | Qué hace |
| --- | --- |
| `W` `A` `S` `D` | Mueven la cámara sobre la imagen |
| `G` | Activa/desactiva el ajuste a cuadrícula |
| `L` | Muestra/oculta las etiquetas de las cajas |

**Deshacer, copiar, guardar**

| Tecla | Qué hace |
| --- | --- |
| `Ctrl+Z` / `Ctrl+Y` | Deshacer / rehacer |
| `Ctrl+D` | Duplica la caja seleccionada |
| `Ctrl+A` | Selecciona todas las cajas del mismo tipo |
| `Ctrl+C` / `Ctrl+V` | Copia / pega todas las paredes |
| `Ctrl+Shift+C` / `Ctrl+Shift+V` | Copia / pega solo la caja seleccionada |
| `Ctrl+L` | Vuelve a cargar lo último guardado (descarta cambios) |
| `ENTER` | **Guarda** en `Hitboxes/<nombre_del_fondo>_hitboxes.json` |
| `ESC` | Salir |

Guarda con `ENTER` varias veces mientras trabajas, no solo al final. Si
cierras y vuelves a abrir con el mismo fondo, retoma lo que habías guardado.

**Probar las paredes que dibujaste**

| Tecla | Qué hace |
| --- | --- |
| `T` | Entra/sale del modo de prueba |
| `W` `A` `S` `D` (en modo prueba) | Caminas con un muñeco que choca de verdad contra las paredes |
| `P` | Devuelve el muñeco al punto de inicio |
| `Shift+P` | Define dónde está ese punto de inicio (donde tengas el mouse) |

Este modo es la forma de confirmar que las paredes quedaron bien puestas
antes de darlas por terminadas: si puedes atravesar algo que debería ser
sólido, falta una caja ahí.

## 4. Editor de personaje

### Antes de correrlo

Pon el sprite del personaje dentro de `Imagenes/Personajes/` (puede ser un
PNG suelto, no hace falta subcarpeta).

### Cómo correrlo

```
python Editores/personaje_editor.py
```

Se abre un selector con todos los personajes encontrados. Navega con las
flechas o el mouse, `Ctrl+F` para buscar por nombre, `ENTER` para abrir el
que quieras. Desde el editor, `ESC` te devuelve al selector.

### Controles

Verás el sprite con dos rectángulos: uno **rojo** (colisión, con qué choca el
personaje) y uno **amarillo** (interacción, el área donde otro jugador puede
interactuar con él). Arriba siempre se ven los valores actuales.

| Tecla | Qué hace |
| --- | --- |
| `I` | Cambia cuál de los dos hitboxes estás editando (rojo / amarillo) |
| `Q` / `E` | Achica / agranda el sprite (escala) |
| `A` / `D` | Achica / agranda el ANCHO del hitbox activo |
| `W` / `S` | Achica / agranda el ALTO del hitbox activo |
| Flechas | Mueven la POSICIÓN del hitbox activo |
| `R` | Restablece todo a los valores por defecto |
| `Ctrl+Z` / `Ctrl+Y` | Deshacer / rehacer |
| `ENTER` | **Guarda** |
| `ESC` | Volver al selector |

Lo normal es que el hitbox rojo quede pequeño y cerca de los pies del
personaje (es donde choca con el suelo y las paredes, no todo el dibujo). El
amarillo suele ser un poco más grande, para que sea fácil acercarse e
interactuar.

## 5. Cuando termines

Los `.json` quedan guardados solos en la carpeta `Hitboxes/`. No hay que
mandárselos a nadie por aparte: cuando hagas `git add` / `git commit` /
`git push` del proyecto se suben con todo lo demás. Avísale a Diego cuando
tengas los hitboxes listos.

## 6. Lo que puedes ignorar

Estos editores traen funciones del proyecto anterior (EmpatiaQuest, un RPG de
colegio) que en Alcalde Digital no usamos. Si ves estas teclas en pantalla o
las presionas sin querer, no te preocupes — pero no las necesitas:

- `O` — cambia al "modo objeto" para colocar muebles y decoración. Ese modo
  usa una carpeta `Objetos/` con los muebles de EmpatiaQuest que aquí no
  existe, así que no hay nada que colocar.
- `N`, `B`, `1`, `2`, `Shift+1`, `Shift+2` — colocar NPCs (Sara, Diego) y
  elegirles animaciones. Son personajes de EmpatiaQuest.
- `J`, `H`, `K` — elegir el fondo destino de una puerta y el tipo de acción
  del interactuable. Tienen sentido en un juego con varias escenas
  conectadas por puertas; aquí todavía no.
- `R`, `[`, `]` — recortar y ajustar frames de objetos de decoración.
- **`alineacion_editor.py`** — este tercer editor sirve para alinear un
  personaje sentado con un pupitre. Alcalde Digital no tiene ni pupitres ni
  personajes sentados, así que no lo abras: además de no servir, escribe
  constantes de EmpatiaQuest dentro de `config.py` del proyecto.
