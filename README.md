# KiCad Grid Checker Plugin

A KiCad 9 action plugin that checks whether vias and components are positioned on a user-defined grid.

![Plugin Icon](resources/icon.png)

## Features

- Check **vias** and/or **footprints** against a configurable grid size (e.g. 0.5mm, 0.25mm, 1.0mm)
- **Strict mode**: both X and Y must be on grid, or **lenient mode**: at least one axis on grid
- Off-grid items are **selected** (highlighted) in the PCB editor
- Optional **persistent visual markers** on the User.9 layer (red circles for vias, blue for components)
- One-click marker cleanup

## Installation

### Manual

Copy the plugin folder into your KiCad scripting plugins directory:

| OS      | Path                                          |
| ------- | --------------------------------------------- |
| Windows | `Documents\KiCad\9.0\scripting\plugins\`      |
| Linux   | `~/.local/share/kicad/9.0/scripting/plugins/` |
| macOS   | `~/Documents/KiCad/9.0/scripting/plugins/`    |

```
cp -r plugins/ /path/to/kicad/scripting/plugins/CheckGridPlugin/
```

Restart KiCad's PCB editor after copying.

### KiCad Plugin and Content Manager (PCM)

This plugin can also be installed via the KiCad PCM if added to a PCM repository.

## Usage

1. Open a PCB in KiCad's PCB editor
2. Go to **Tools > External Plugins > Grid Checker** (or click the toolbar button)
3. Configure the grid size, what to check, and checking mode
4. Click **Run Check**

Off-grid items will be selected and optionally marked with colored circles on the User.9 layer. Use the **Clear Markers** button to remove them.

## License

MIT
