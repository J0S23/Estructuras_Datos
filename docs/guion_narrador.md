# Guion de las voces (narrador y agentes)

Cada línea de abajo es **un archivo de audio**. Se guardan con el nombre
exacto de la tabla en `Audio/Narrador/` (MP3 o WAV). El juego los reproduce
solo (`juego/voces.py`) junto al texto: la cinemática, los finales y el
diálogo de la sala. Si falta uno, esa parte sale solo en texto.

Hay dos tipos de voz:

- **El narrador lo graba un amigo** (voz real): la cinemática del inicio y
  los cinco finales (secciones 1 y 3).
- **Los cuatro agentes van con voces de IA** (ElevenLabs): lo que dicen en
  la sala de los niños (secciones 2 y 4).

Los números van escritos en letras (así se lee "once y cuarenta y siete" y
no "once cuarenta y siete p eme"). Los puntos suspensivos (...) son una
pausa. Acento latinoamericano (colombiano, ojalá), no de España.

## Cómo grabar al narrador (el amigo)

- **El tono:** adulto, calmado, tipo documental. Serio, sin exagerar como en
  un tráiler. Lento: el texto sale escrito en pantalla al mismo tiempo y
  tiene que alcanzar a leerse.
- **Dónde:** un cuarto pequeño y callado (con ropa o cobijas alrededor
  suena menos a eco). Sin ventilador ni aire acondicionado.
- **Con qué:** el celular sirve (la app de grabadora), a un palmo de la boca
  y un poco de lado, para que la P y la B no golpeen el micrófono. Siempre a
  la misma distancia, para que todas las líneas suenen igual.
- **Cada línea, dos o tres veces**, y se escoge la mejor. Medio segundo de
  silencio antes y después.
- Se recorta, se exporta y se le pone el nombre de la tabla (por ejemplo,
  con Audacity, que es gratis).

## Cómo hacer las voces de los agentes (ElevenLabs)

1. En ElevenLabs, **Text to Speech**: se escoge una voz de la biblioteca
   (filtrar por español latinoamericano) o se crea una con **Voice Design**
   describiéndola.
2. Una voz fija para cada agente, siempre la misma. Que vaya con su
   personaje y su sprite (el equipo decide si es de hombre o de mujer):
   - **Tecnomante:** joven, rápida y precisa, un poco nerviosa.
   - **Forjador:** más grave, firme, de pocas palabras.
   - **Biomante:** cálida y suave, la más conmovida.
   - **Resonante:** baja, casi en susurro, como quien está escuchando algo.
3. Más bajito y conmovido que en una conversación normal: están viendo algo
   muy fuerte. En ElevenLabs, subir un poco **Stability** para que no
   exagere y bajar **Style**.
4. Se pega la línea, se genera, se descarga y se guarda con el nombre de la
   tabla.

El plan gratis de ElevenLabs pide dar crédito: en los créditos del juego va
"Voces de los agentes generadas con ElevenLabs", y Lucas Manjarrez como
narrador.

## 1. Cinemática del inicio (narrador)

| Archivo | Texto |
| --- | --- |
| `apertura_1.mp3` | Una habitación a oscuras. Once y cuarenta y siete de la noche. Una niña de once años chatea en NEXUS con la cuenta de su cantante favorita... Le escribe su dirección. Y la envía. |
| `apertura_2.mp3` | Esa misma semana, en otras pantallas. Un niño comparte su ubicación en vivo para entrar a un reto. Otro sube una foto con el uniforme y el nombre de su colegio. A otro, una cuenta nueva le escribe: "No le cuentes a tus papás". |
| `apertura_3.mp3` | Esa noche... una luz verde cae sobre cada una de esas casas. A la mañana siguiente hay camas vacías... y un celular en el piso. |
| `apertura_4.mp3` | Un mes después. Desaparecen cientos de niños en todo el mundo, pero en NEXUS nadie habla de ellos. Lo que se publica sobre ellos se borra en minutos. |
| `apertura_5.mp3` | Una sala del gobierno de Colombia. Los famosos de NEXUS dicen lo mismo, a la misma hora. Una nave invisible orbita la Tierra. Arman una misión secreta con cuatro agentes. Ellos tampoco saben qué van a encontrar. |
| `apertura_frase.mp3` | Allá arriba... la mentira también tiene cuenta. |

## 2. Al ver a los niños (agentes, IA)

| Archivo | Quién | Texto |
| --- | --- | --- |
| `ninos_1.mp3` | Biomante | Son niños... están dormidos. Todavía respiran. |
| `ninos_2.mp3` | Tecnomante | Son los niños desaparecidos. Los de las noticias que NEXUS borraba. |
| `ninos_3.mp3` | Resonante | Esa niña tiene el celular en la mano. Le escribieron haciéndose pasar por alguien famoso. |
| `ninos_4_pistas3.mp3` | Forjador | La mochila, el zapato, el dibujo... eran de ellos. Las cápsulas no se abren: están soldadas a la nave. |
| `ninos_4_pistas2.mp3` | Forjador | Lo que encontramos en la nave era de ellos. Las cápsulas no se abren: están soldadas a la nave. |
| `ninos_4_pistas1.mp3` | Forjador | Lo que encontramos en la nave era de uno de ellos. Las cápsulas no se abren: están soldadas a la nave. |
| `ninos_4_pistas0.mp3` | Forjador | Por eso nadie hablaba de ellos en NEXUS. Las cápsulas no se abren: están soldadas a la nave. |
| `ninos_5.mp3` | Biomante | Esa luz estaba prendida hace un momento... |
| `ninos_6.mp3` | Resonante | ¿Oyen eso? Hay un celular en el piso, en medio de la sala. No para de vibrar. |

(La línea del Forjador tiene cuatro versiones: depende de cuántas pistas
encontraron en la nave. Se hacen las cuatro.)

### Cuando ese agente no está en la partida

Si falta el rol de una línea, la dice otro agente. **Nunca suena con la voz
de otro personaje**: el juego busca a alguien de la partida que tenga esa
línea grabada con su propia voz (`<archivo>_<rol>.mp3`, por ejemplo
`ninos_1_tecnomante.mp3`); si nadie la tiene, sale solo el texto. Con dos
versiones extra por línea ya se cubre cualquier pareja de jugadores:

| Archivo (texto igual al de arriba) | Voz |
| --- | --- |
| `ninos_1_resonante.mp3`, `ninos_1_tecnomante.mp3` | Resonante, Tecnomante |
| `ninos_2_forjador.mp3`, `ninos_2_biomante.mp3` | Forjador, Biomante |
| `ninos_3_biomante.mp3`, `ninos_3_tecnomante.mp3` | Biomante, Tecnomante |
| `ninos_4_pistas3_tecnomante.mp3` ... `ninos_4_pistas0_tecnomante.mp3` (las cuatro) | Tecnomante |
| `ninos_4_pistas3_resonante.mp3` ... `ninos_4_pistas0_resonante.mp3` (las cuatro) | Resonante |
| `ninos_5_resonante.mp3`, `ninos_5_forjador.mp3` | Resonante, Forjador |
| `ninos_6_biomante.mp3`, `ninos_6_forjador.mp3` | Biomante, Forjador |
| `sala_esperar_biomante.mp3`, `sala_esperar_forjador.mp3`, `sala_esperar_resonante.mp3` | (la piensa el que intenta entrar: una por cada voz) |

El cuadro del diálogo dura lo mismo que su audio, y mientras alguien habla
con voz nada lo interrumpe: los avisos de NEXUS, los logros y NEILA esperan
a que termine, y la línea siguiente no empieza hasta que acaba la anterior.

## 3. Los finales (narrador)

| Archivo | Texto |
| --- | --- |
| `final_sin_entrar.mp3` | Los famosos alienígenas quedan expuestos, y NEXUS deja de ser la voz de la nave. Pero nunca sabrán lo que había detrás de esa pared... Y los niños siguen arriba. |
| `final_escaparon.mp3` | Por primera vez, NEXUS habla de los niños. La noticia es real, y millones de personas la comparten. Los niños siguen arriba... pero ya nadie puede esconderlos. |
| `final_quedarse.mp3` | Los encierran en la nave, junto a los niños. La pantalla se apaga... y NEXUS sigue publicando como si nada. En la Tierra, nadie sabrá nunca lo que encontraron. |
| `final_liberados.mp3` | Los niños se van en la cápsula. Los agentes se quedan atrás, tapando la puerta. A la mañana siguiente, en la Tierra, una niña despierta en su cuarto... Los agentes no volvieron. Pero esta vez, todos hablan de los niños. |
| `final_nadie.mp3` | Nadie decidió. Se quedaron en la nave. El Guardia de la Bahía suelta la fruta y destruye la cápsula. Los capturan a todos. NEXUS publica: "Agentes colombianos difundían noticias falsas". |
| `final_frase.mp3` | Ellos compartieron su dirección... Tú decides qué compartes. |
| `final_frase_liberados.mp3` | Ellos compartieron su dirección... Ustedes compartieron su lugar. |

(`final_frase_liberados` es la frase del final en que liberan a los niños;
los demás finales usan `final_frase`.)

Las grabaciones de Lucas se limpiaron (ruido de fondo, silencios del
principio y el final) y quedaron al mismo volumen. Los subtítulos aparecen
cuando él empieza a decir cada línea: las marcas están en
`Audio/Narrador/cortes.json`. Si se cambia un audio o un texto, hay que
correr `python Audio/generar_cortes.py` (usa ffmpeg); sin la marca, los
subtítulos se reparten parejo, como antes.

## 4. En la sala y la votación (agentes, IA; opcional)

Frases cortas que dicen durante la historia. Si no da el tiempo, se pueden
dejar solo en texto. Cada una va con la voz de un agente (`POR_DEFECTO` en
`juego/voces.py`: las de la Biomante, la Resonante, el Tecnomante y el
Forjador); en la partida la dice alguien que la tenga grabada con su voz, y
se le pueden agregar versiones con otras voces (`<archivo>_<rol>.mp3`).

| Archivo | Texto |
| --- | --- |
| `sala_abierta.mp3` | ¿Escucharon eso? Algo se abrió en la pared, al lado de la cápsula... |
| `sala_esperar.mp3` | Quizá debería esperar a mis amigos antes de entrar por ahí. |
| `regenerar.mp3` | Lo intento... pero mi regeneración ya no encuentra nada que curar. (Biomante) |
| `vidrio_sin_martillo.mp3` | El vidrio es grueso. Con algo pesado se podría romper... |
| `vidrio_con_martillo.mp3` | Con el martillo podría romper el vidrio... Hay que decidirlo juntos. |
| `voto_escapar.mp3` | ¡A la cápsula, ya! ¡Corran! |
| `voto_quedarse.mp3` | No los vamos a dejar solos. |
| `voto_liberar.mp3` | ¡Rompe el vidrio! ¡Los sacamos de aquí! |
| `liberar_sube.mp3` | ¡Arriba, rápido! ¡Nosotros nos quedamos! |
