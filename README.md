# NEXUS

*En el vacío, nada está realmente solo.*

Videojuego educativo en Python/Pygame sobre el uso responsable de las redes
sociales. Proyecto de laboratorio de **Estructura de Datos II**, Universidad
del Norte.

Cuatro personas fueron secuestradas por una nave alienígena y despiertan en
una prisión. Para escapar tienen que trabajar juntas: encontrar el código de
la puerta, apagar las consolas de navegación, reparar una cápsula y llegar a
ella sin que los aliens las atrapen. No hay armas: solo sigilo, las
habilidades de cada rol (Tecnomante, Forjador, Biomante y Resonante) y la
**NEXUS**, la red social de la nave, donde uno de los que escriben es un
alien disfrazado de prisionero. Se juega de 2 a 4 personas en la misma
pantalla, partida en una vista por jugador.

## Estructuras de datos

| Estructura | Donde | Para que |
|---|---|---|
| Arbol binario de comportamiento | `Estructuras/arbol_comportamiento.py` | La "IA" de cada alien: cada frame baja de la raiz a una hoja respondiendo preguntas (¿ve a alguien?, ¿oye un ruido?) y la hoja dice que hace. Se ve en vivo en Pausa > Opciones > Arbol del alien. |
| Arbol binario de habilidades | `Estructuras/arbol_habilidades.py` | Progresion de cada rol durante la ronda. Al subir se escoge **una de dos** ramas y la otra se cierra, asi que lo desbloqueado cambia las opciones que el jugador ve. Recorrido por niveles (BFS) para dibujarlo y preorden para descartar la rama perdida. |
| Arbol N-ario de logros | `Estructuras/arbol_logros.py` | Los logros de la partida, como los de Minecraft: cada uno abre otros. Indice clave -> nodo, subir por los padres hasta la raiz al conseguir uno, BFS por niveles, preorden para moverse por la vista y postorden para ubicar cada nodo al dibujarlo. Pausa > Logros. |
| Arbol de comportamiento del Cambiaformas | `data/comportamiento_cambiaformas.py`, `cambiaformas.py` | Otro arbol binario de decision con la misma clase: ¿fuera de combate? ¿huyendo? ¿lo llevan creyendo que es un prisionero? ¿ya se revelo? ¿la presa se escondio? ¿esta cerca y sola? ¿tiene presa? ¿hay un rumor de carnada? -> seguir (y traicionar), acechar, revelarse, perseguir, revisar escondite, huir... |
| Grafo de la nave (BFS) | `navegacion.py` | Los aliens buscan camino por una cuadricula del mapa (cada celda es un nodo) para llegar a un ruido rodeando paredes. |
| Grafo dirigido de NEXUS | `Estructuras/grafo.py`, `nexus.py` | La red social del celular. Cada cuenta es un nodo y "lo que publica A le llega a B" es una arista (lista de adyacencia). Los rumores y los desmentidos se propagan con **BFS por niveles** (un nivel por tick); "¿de donde salio esto?" es el **camino mas corto** desde el bot que lo empezo; reportar un bot es **borrar su nodo**; las barras de confianza son el % de nodos verdes y rojos. |

## Como correrlo

Requiere Python 3 y Pygame (`pip install pygame`).

```bash
python main.py                        # el juego
python pruebas/prueba_partida.py      # una ronda completa sin abrir ventana
python pruebas/prueba_seleccion.py    # el flujo de cantidad y roles, a 2, 3 y 4
python pruebas/prueba_controles.py    # que nadie se robe las teclas de otro
python pruebas/prueba_paneles.py      # los paneles a varias resoluciones
python pruebas/prueba_estructuras.py  # los arboles por consola
python pruebas/prueba_textos.py       # que la fuente pueda dibujar todo el texto
```

### Como se juega

Al darle **Jugar** se pregunta primero cuantos juegan (2, 3 o 4) y despues cada
uno escoge su rol desde su propia seccion de pantalla. Dos jugadores no pueden
quedarse con el mismo rol. Ya en partida, cada uno se mueve por la nave en su
trozo de pantalla y usa su tecla de interaccion con lo que tenga cerca.

| | Jugador 1 | Jugador 2 | Jugador 3 | Jugador 4 |
|---|---|---|---|---|
| Moverse | WASD | Flechas | mando: stick o cruceta | mando: stick o cruceta |
| Interactuar / confirmar | E | Enter | A (o O) | A (o Y) |
| Elegir opcion | W / S | Flecha arriba / abajo | stick / cruceta (o I / K) | stick / cruceta (o T / G) |
| Arbol de habilidades | Q | Shift derecho | Y (o U) | Y (o R) |
| Usar habilidad | F | - (junto al Shift derecho) | X (o P) | X (o V) |
| Caminar en sigilo (mantener) | Shift izquierdo | AltGr o 0 del numerico | LB o LT | LB o LT |
| Celular (NEXUS): abrir / atras | TAB | . (punto) | RB (o J) | RB (o B) |
| Cerrar un panel | - | - | B | B |

Los jugadores 3 y 4 juegan con mando (Xbox o parecido): el primero que se
conecta es del jugador 3 y el segundo del 4. Sin mando escogen rol con las
letras del teclado pero en partida no se mueven. En los menus el mando hace de
flechas y Enter. `python pruebas/probar_mando.py` muestra que boton manda cada
cosa por si algun mando sale con los numeros cambiados (se ajusta en `mandos.py`). No hay tecla de correr; la de sigilo hace caminar a la
mitad de velocidad y casi sin ruido.

Teclas globales: **[F11]** alterna ventana y **[ESC]** (o START en el mando) abre el
menu de pausa: continuar, opciones, logros y terminar partida. En Opciones, ademas del
sonido y la pantalla completa, estan las vistas para probar: apagar el campo de vision y
la oscuridad, ver las hitboxes y ver el arbol de comportamiento de cada alien en vivo. La mision dura siete minutos y termina en una pantalla de resultados, desde donde se puede ver el arbol de logros de la partida.

Ademas hay editores para preparar los assets:

```bash
python Editores/editor_mapa.py       # poner aliens, escondites, terminales... (ver abajo)
python Editores/hitbox_editor.py     # dibujar las hitboxes de un mapa
python Editores/personaje_editor.py  # calibrar escala e hitbox de un personaje
python Editores/visor_personajes.py  # revisar que sprites y config tiene cada personaje
```

### NEXUS: la red social en el celular

Cada jugador tiene NEXUS en su celular. Los aliens (el Cambiaformas, con cuentas
falsas que parecen prisioneros) riegan **rumores falsos** sobre lugares de la nave
("la capsula exploto", "las celdas tienen gas"...). Con el celular se puede:

- **Ir a verificarlo**: una flecha lleva al lugar; al llegar se saca una foto sola.
- **Desmentir** con la foto: la verdad corre por la red y la tripulacion confia en
  ustedes. La foto tal cual convence a mas gente, pero se ve donde estas y el alien
  mas cercano va por ti; recortada es mas segura.
- **Compartir**: compartir un rumor sin verificar lo riega mas y tus seguidores
  dejan de confiar en ti.
- **¿De donde salio esto?** y **reportar**: reportar al bot que lo empezo lo borra
  de la red; reportar a un prisionero que solo se lo creyo no sirve de nada.

Arriba al centro esta la **barra de confianza** de la tripulacion, una sola para
todo el equipo: la parte **verde** (confian en ustedes) crece desde la izquierda, la
**roja** (le creen a los aliens) desde la derecha y en medio queda gris (los que no
deciden). Con la verde en 80% (la raya blanca) les pasan los **planos de la capsula**
(sin ellos no se puede reparar). Mientras la roja le gana a la verde, los aliens son
mas rapidos y ven mas lejos; si la roja llega al 90%, los aliens toman NEXUS y se
pierde. Con el celular abierto no te mueves: si un alien llega, te atrapa. Al final,
los resultados muestran como usaron NEXUS. Cuentas, rumores y numeros se editan en
`data/nexus.py`.

Las **Terminales NEXUS** del mapa son centrales de ayuda: muestran como va la
confianza, cuanto falta para los planos y que rumores faltan por desmentir, y
explican el uso sano de la red (como reconocer un rumor falso, cuidar la ubicacion,
cuentas falsas y reportes). Tambien dejan repasar el tutorial y, por ahora, abrir
el caso del infiltrado.

### Los prisioneros y el Cambiaformas

Por la nave caminan 6 prisioneros, cada uno con su nombre de NEXUS encima y un
puntito de color: los **verdes** (confian en ustedes) dan pistas al pasar cerca,
los **grises** solo charlan y los **rojos** a veces gritan donde estas.

Uno de ellos no es un prisionero: es el **Cambiaformas**, un alien unico con su
propio arbol de comportamiento. Escoge a la presa mas sola, la sigue disfrazado y,
cuando la tiene cerca, se revela (susto) y corre mas rapido que nadie un rato. Si
falla, huye, se disfraza de otro prisionero y vuelve por la misma presa. Revisa el
casillero donde te vio esconderte, espera junto al lugar de sus rumores y se entera
cuando alguien te delata. Pistas: no habla, su nombre falla, puede haber dos con el
mismo nombre, el Escaneo y la Sintonia lo marcan y disfrazado no sube el pulso.
El hackeo lo aturde y le quita el disfraz; el **caso del Cambiaformas** (3 pruebas
subidas en una Terminal NEXUS, los sospechosos son los prisioneros que caminan) lo
deja 60 s sin poder disfrazarse. Numeros en `data/npcs.py`.

Tambien **suplanta** cuentas: publica en NEXUS como el prisionero que imita para
citar a alguien en un lugar apartado y emboscarlo. "¿De donde salio esto?" muestra
"dispositivo desconocido"; reportar la suplantacion lo deja al descubierto. Cerca
de el, disfrazado, se oye un **susurro**.

**Rescatar prisioneros:** con la tecla de interactuar junto a un prisionero le
preguntas "¿vienes conmigo?". Los verdes te siguen, los grises dudan y los rojos
no. Llevarlo a la capsula da puntos y publica un testimonio que riega confianza.
Ojo: el Cambiaformas disfrazado tambien acepta (sin decir nada) y te traiciona:
si te quedas solo con el, se revela; si llega con el grupo a la capsula, la
sabotea (arranca una pieza o deshace parte de la reparacion). Los verdes te
advierten si vas con el.

### La mision (mapa de la nave)

Cuatro prisioneros escapan de una nave alienigena en tres fases: abrir la
puerta de la prision con el codigo que esta en una de las notas, apagar las
consolas de navegacion y reparar la capsula de escape; despues los aliens
entran en alerta y todos tienen que llegar a la capsula. Si atrapan a alguien
va a una celda y otro lo tiene que sacar. Cada jugador tiene 3 vidas (los
corazones arriba a la izquierda): a la tercera captura queda eliminado. La
Biomante puede devolver vidas con Regeneración. Si eliminan al Tecnomante deja dos decodificadores, y si eliminan
al Forjador deja un kit de herramientas, para que la mision se pueda terminar.
Lo que lleva cada uno se ve en el inventario, abajo a la derecha. Las consolas y la reparacion se hacen
**manteniendo** la tecla de interactuar. La habilidad escogida se usa con **F**
(jugador 1) o **-** (jugador 2, la tecla junto al Shift derecho) y se paga con puntos del equipo.

Cada jugador tiene un **campo de vision**, como en Among Us: no ve a traves de
las paredes ni de las compuertas bajadas; lo que queda detras se ve en penumbra
y los aliens que esten ahi no se dibujan. Si sale el evento de **apagon** todo
queda a oscuras (cada uno ve lo que alumbra su linterna, que tampoco atraviesa
paredes; de los aliens no se ven ni los ojos ni su rango de vision, y sus
señales quedan a oscuras como ellos) y no funciona nada electrico: terminales,
NEXUS, escaneo, teclados, consolas, puertas para dos y los sellos del Forjador.
Dura hasta que alguien encuentre la caja de fusibles que parpadea en rojo y la
encienda manteniendo la tecla. Hay cuatro tipos de alien
(Rastreador, Vigia, Ciego y Cazador) con el mismo arbol de comportamiento y
distintos sentidos. Cada minuto, mas o menos, la nave lanza un evento al azar
(apagon, alarma o cierre de una compuerta; solo puede haber un apagon a la vez), y la puerta a la sala de control se
abre solo con dos jugadores, cada uno en un panel. La partida empieza con un
tutorial sin tiempo: cada jugador pasa los pasos con su tecla de habilidad, y los
aliens despiertan (y la puerta de la prision deja meter el codigo) solo cuando
todos terminaron.

Mision secundaria (opcional), idea de Joseph: **el infiltrado**. Uno de los que
escriben en NEXUS es un alien cambiaformas. Por la nave hay tres pruebas (audio,
expediente y captura de camara); cada una revela un rasgo suyo y, al subirla
desde una Terminal NEXUS, descarta sospechosos. Con las tres queda expuesto y los
aliens se quedan confundidos 20 s. Se puede acusar antes, pero si fallan el caso
se cierra y la nave delata al que acuso.

```bash
python pruebas/prueba_mision.py    # juega la mision completa sin ventana
python pruebas/prueba_sorpresas.py # oscuridad, aliens, sigilo, eventos, puertas, tutorial
python pruebas/prueba_vision.py    # campo de vision: las paredes tapan
python pruebas/prueba_nexus.py     # NEXUS: grafo, rumores, celular, barras y planos
python pruebas/prueba_cambiaformas.py # prisioneros que caminan y el Cambiaformas
python pruebas/prueba_infiltrado.py # mision secundaria del infiltrado de NEXUS
python pruebas/prueba_logros.py    # arbol de logros y cuando se consigue cada uno
python pruebas/prueba_sonidos.py   # que todo sonido pedido exista y suene donde va
python pruebas/simulador.py 8      # bots que juegan 8 partidas: bugs y balance
python pruebas/prueba_hud.py       # capturas del HUD con 2, 3 y 4 jugadores
```

### Editar el mapa sin tocar codigo

`python Editores/editor_mapa.py` abre el mapa y deja poner con el mouse todo lo
que va encima: inicio de los jugadores, rutas de los aliens, escondites,
celdas, puerta de la prision, notas, consolas, capsula, piezas, terminales NEXUS,
terminales y paneles de los roles, consumibles, compuertas, puertas para dos,
cajas de fusibles y pruebas del infiltrado (la lista con sus teclas
esta en el editor). Clic izquierdo pone o arrastra, clic derecho borra, `Ctrl+S` guarda,
`M` hace que el juego use ese mapa y `F5` guarda y abre el juego para probar.
Marca en rojo lo que choca con paredes y en naranja lo que no se alcanza
caminando. Guarda en `Hitboxes/<mapa>_objetos.json`; las paredes se siguen
dibujando con `hitbox_editor.py`. Para un mapa nuevo: dibujar sus paredes con
el editor de hitboxes y despues poner todo lo demas con el editor de mapa.

```bash
python pruebas/prueba_editor_mapa.py  # el editor y que el juego use lo guardado
```

## Estructura del repositorio

- `Estructuras/` -- los arboles y sus nodos.
- `jugador.py` -- un jugador: su personaje, rol, puntos y arbol de habilidades.
- `pruebas/` -- pruebas que corren sin abrir ventana.
- `Movimiento/` -- carga de sprites, animaciones y movimiento de personajes.
- `screens/` -- las pantallas del juego (menu, seleccion, partida, paneles, ayuda...).
- `Editores/` -- herramientas para hitboxes y calibracion de personajes.
- `Imagenes/` -- assets: `Fondos/` (la nave y el menu), `Personajes/<Rol>/`
  (`<Rol>_<animacion>_<direccion>.png`), `Aliens/` y `Objetos/`.
- `Hitboxes/` -- los JSON que generan los editores (paredes, objetos del mapa,
  hitbox de cada rol). La nave es el unico mapa.
- `data/` -- datos del juego: roles, habilidades, aliens, logros, infiltrado, notas...