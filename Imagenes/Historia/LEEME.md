# Imágenes de la historia de los niños

Todo lo de la historia (la cinemática de apertura, la sala oculta y los
finales) se dibuja con código mientras no haya arte. Para cambiar un dibujo
por uno de verdad basta con poner aquí un PNG con el nombre de la lista: el
juego lo usa solo, sin tocar código (`screens/arte_historia.py`, función
`imagen`). Se recorta lo transparente de los bordes y se escala con nearest
(pixel art).

| Archivo | Qué reemplaza | Tamaño sugerido |
| --- | --- | --- |
| `nino_0.png` ... `nino_9.png` | Cada niño (de frente, quieto). El 0 es la niña de la cinemática (pijama morado, con el celular). Dormidos en la sala; en la cinemática, despiertos. | 15 x 30 px, o el sprite que hagan (se escala) |
| `capsula.png` | La cápsula de cristal VACÍA (el vidrio transparente o semitransparente: el niño se dibuja adentro). Hoy es la cápsula de energía `OBJ-039` estirada y en verde. | ~40 x 83 px |
| `capsula_apagada.png` | La cápsula de un niño que no lo logró: sin luz, el líquido turbio, el niño casi no se ve (mismo tamaño que `capsula.png`, CON el niño adentro). Hoy es la misma cápsula oscurecida por código. | ~40 x 83 px |
| `mochila.png`, `zapato.png`, `dibujo.png` | Las pistas del Acto 2 (en el piso de la nave). | ~14 x 14 px |
| `escena_1.png` ... `escena_5.png` | El fondo de cada escena de la cinemática de apertura (el celular, los textos y los personajes van encima). 1: la habitación de noche; 2: fondo de las tres pantallas; 3: la calle de noche; 4: fondo del feed de NEXUS; 5: la sala del gobierno. | 320 x 180 px (16:9) |

Los textos (lo que dicen los agentes, la votación, los finales, la
cinemática) están en `data/historia.py`. Los sonidos de los aliens que vienen
son `Audio/SFX/gritos_aliens_1.ogg` y `gritos_aliens_2.ogg`; los pitidos de los monitores de las
cápsulas, `monitor_bip`, `monitor_falla` y `monitor_plano` (Audio/generar_sonidos.py).
