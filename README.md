# TermCell

A CSV editor for the terminal, with minimal spread sheet capabilities.

**WIP | Work In Progress** this is not a complete project.

## Features

- **Vim-style modal editing** with key chords and commands
- **Full CSV/TSV support** with configurable delimiters
- **Excel-like formulas** (`=SUM(A1:A10)`, `=SUM(B1:B5)`, etc.)
- **Copy/paste integration** with system clipboard
- **Multiple themes** (dark, light, VS Code, Monokai, etc.)
- **Formula calculation** and cell referencing
- **Row/column operations** (insert, delete, resize)
- **Keyboard-driven interface** with minimal mouse dependency

### To do...
- **Undo/redo** with 30-step history (minimal integration)
- **Search and replace** with regex support

## Installation

Clone repository:

`git clone https://github.com/xqtr/termcell`

Change directory:
`cd termcell`

Install requirements
`pip install -r requirements.txt`

For pyperclip to work properly, you may need:
- `xclip or xsel` (for X11)
- `wl-clipboard` (for Wayland)

On Ubuntu/Debian:
`sudo apt-get install xclip xsel`

 On Fedora/RHEL:
`sudo dnf install xclip xsel`

Execute:
`./termcell <filename>`

## Keys

All key bindings, commands, variables, formulas can be read in the HELP.md

### Showcase

![main](https://cp737.net/files/termcell/main.png)
![editor](https://cp737.net/files/termcell/editor.png)
![editor column](https://cp737.net/files/termcell/editor2.png)
![fixed row](https://cp737.net/files/termcell/fixedrow.png)
![theme](https://cp737.net/files/termcell/theme.png)
![open dialog](https://cp737.net/files/termcell/open.png)
![help](https://cp737.net/files/termcell/help.png)
![dialog](https://cp737.net/files/termcell/dialog.png)


## Licence

GPL-3.0-or-later

## Support

For issues and questions, please check the issues page or create a new issue with detailed description.
