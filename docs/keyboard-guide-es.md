# Guía de teclas y controles — LUE

Guía completa del teclado y el mouse en LUE (lector de libros con TTS).
Si usás el perfil **vim** (`keys_vim.json`), las diferencias están al final.

## Navegación de lectura

| Tecla | Acción |
|-------|--------|
| `l` | Párrafo siguiente |
| `h` | Párrafo anterior |
| `k` | Frase siguiente |
| `j` | Frase anterior |
| `i` | Página arriba |
| `m` | Página abajo |
| `u` | Scroll hacia arriba |
| `n` | Scroll hacia abajo |
| `t` | Ir al primer párrafo visible |
| `x` | Capítulo siguiente |
| `z` | Capítulo anterior |
| `y` | Ir al comienzo del libro |
| `b` | Ir al final del libro |

## Control de voz (TTS)

| Tecla | Acción |
|-------|--------|
| `p` o `Espacio` | Reproducir / pausar |
| `,` | Bajar velocidad |
| `.` | Subir velocidad |
| `s` | Resaltado de frase on/off |
| `w` | Resaltado de palabra on/off |

## Ventanas y funciones

| Tecla | Acción |
|-------|--------|
| `c` | Índice de capítulos (flechas o `j`/`k` para moverse, `Enter` salta) |
| `/` | Buscar texto (solo con la voz pausada; `Enter` busca, navega resultados, `Esc`/`/` cierra) |
| `N` | Escribir una nota (se guarda en `~/Documentos/<libro>.md`; `Enter` guarda, `Esc` cancela) |
| `o` | Voces: elegir idioma y voz (Enter aplica y sigue leyendo con la nueva voz) |
| `d` | **Dejar una marca** en la posición actual (punto de salvado, con confirmación en pantalla) |
| `f` | **Marcas guardadas**: ventana con todos los puntos; `Enter` salta a la marca, `x` elimina |
| `a` | Auto-scroll on/off |
| `v` | Cambiar el modo de interfaz (sencilla ↔ completa) |
| `r` | Menú de libros recientes |
| `Enter` | Seleccionar dentro de una ventana |
| `q` | Salir |

## Marcas (puntos de salvado)

- **`d`** guarda una marca en el capítulo/párrafo/frase exacto donde estás
  leyendo, con fecha y hora. Aparece un "✓ Marca N guardada".
- **`f`** abre la lista de marcas del libro: movete con flechas o `j`/`k`
  (con envoltura), `Enter` salta a la marca y cierra, **`x`** elimina la
  marca seleccionada, `f` cierra sin saltar.
- Se guardan en `~/Documentos/LUE/<libro>.bookmarks.json` (una por libro).
  La carpeta `LUE` se crea sola la primera vez.
- Las marcas conviven con las notas (`N`, en `~/Documentos/<libro>.md`) y el
  progreso de lectura (que se guarda solo, igual que siempre).

## Mouse

| Acción | Resultado |
|--------|-----------|
| Click en una frase | Salta la lectura a esa frase (corta el audio actual) |
| Arrastrar sobre el texto | Selecciona y al soltar **copia al portapapeles** ("✓ Copiado") |
| Click en la barra de progreso | Salta a esa parte del libro |
| Rueda | Scroll |

La copia funciona con las herramientas nativas (`wl-copy`, `xclip`, `xsel`,
`pbcopy`, `clip.exe`) y, si no hay ninguna, con la secuencia OSC 52
(terminales, tmux y multiplexores que la reenvíen).

## Diferencias del perfil vim (`keys_vim.json`)

| Acción | Default | Vim |
|--------|---------|-----|
| Párrafo siguiente / anterior | `l` / `h` | `j` / `k` |
| Frase siguiente / anterior | `k` / `j` | `)` / `(` |
| Página arriba / abajo | `i` / `m` | `Ctrl+B` / `Ctrl+F` |
| Scroll arriba / abajo | `u` / `n` | `Ctrl+U` / `Ctrl+D` |
| Primer párrafo visible | `t` | `H` |
| Comienzo / final del libro | `y` / `b` | `g` / `G` |

El resto de las teclas (`p`, `c`, `/`, `N`, `o`, `d`, `f`, `a`, `v`, `r`,
`q`, `Enter`) coincide con el perfil por defecto.
