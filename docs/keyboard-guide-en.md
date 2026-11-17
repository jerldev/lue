# Keyboard and controls guide — LUE

Complete keyboard and mouse reference for LUE (a TTS ebook reader).
If you use the **vim** profile (`keys_vim.json`), differences are listed
at the end.

## Reading navigation

| Key | Action |
|-----|--------|
| `l` | Next paragraph |
| `h` | Previous paragraph |
| `k` | Next sentence |
| `j` | Previous sentence |
| `i` | Page up |
| `m` | Page down |
| `u` | Scroll up |
| `n` | Scroll down |
| `t` | Go to first visible paragraph |
| `x` | Next chapter |
| `z` | Previous chapter |
| `y` | Jump to the beginning of the book |
| `b` | Jump to the end of the book |

## Voice (TTS) controls

| Key | Action |
|-----|--------|
| `p` or `Space` | Play / pause |
| `,` | Decrease speed |
| `.` | Increase speed |
| `s` | Toggle sentence highlight |
| `w` | Toggle word highlight |

## Windows and features

| Key | Action |
|-----|--------|
| `c` | Chapter index (arrows or `j`/`k` to move, `Enter` jumps) |
| `/` | Text search (paused TTS only; `Enter` searches, browse results, `Esc`/`/` closes) |
| `N` | Write a note (saved to `~/Documents/<book>.md`; `Enter` saves, `Esc` cancels) |
| `o` | Voices: pick language and voice (Enter applies and keeps reading with the new voice) |
| `d` | **Drop a bookmark** at the current position (save point, with on-screen confirmation) |
| `f` | **Saved bookmarks**: window listing every mark; `Enter` jumps to it, `x` deletes |
| `a` | Auto-scroll on/off |
| `v` | Cycle UI complexity (simple ↔ full) |
| `r` | Recent books menu |
| `Enter` | Select inside a window |
| `q` | Quit |

## Bookmarks (save points)

- **`d`** saves a bookmark at the exact chapter/paragraph/sentence you are
  reading, timestamped. A "✓ Marca N guardada" message confirms it.
- **`f`** opens the book's bookmark list: move with arrows or `j`/`k`
  (wraps around), `Enter` jumps to the mark and closes, **`x`** deletes
  the selected mark, `f` closes without jumping.
- Bookmarks are stored in `~/Documents/LUE/<book>.bookmarks.json` (one file
  per book). The `LUE` folder is created automatically on first use.
- Bookmarks coexist with notes (`N`, in `~/Documents/<book>.md`) and with
  reading progress (which keeps auto-saving as always).

## Mouse

| Action | Result |
|--------|--------|
| Click a sentence | Jumps reading to that sentence (cuts current audio) |
| Drag over text | Selects and **copies to clipboard** on release ("✓ Copiado") |
| Click the progress bar | Jumps to that part of the book |
| Wheel | Scroll |

Copying works with native tools (`wl-copy`, `xclip`, `xsel`, `pbcopy`,
`clip.exe`) and falls back to the OSC 52 sequence (terminals, tmux and
multiplexers that forward it).

## Vim profile differences (`keys_vim.json`)

| Action | Default | Vim |
|--------|---------|-----|
| Next / previous paragraph | `l` / `h` | `j` / `k` |
| Next / previous sentence | `k` / `j` | `)` / `(` |
| Page up / down | `i` / `m` | `Ctrl+B` / `Ctrl+F` |
| Scroll up / down | `u` / `n` | `Ctrl+U` / `Ctrl+D` |
| First visible paragraph | `t` | `H` |
| Beginning / end of book | `y` / `b` | `g` / `G` |

All other keys (`p`, `c`, `/`, `N`, `o`, `d`, `f`, `a`, `v`, `r`, `q`,
`Enter`) match the default profile.
