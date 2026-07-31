---
title: Installation
summary: Getting Animmix into Maya, on Windows and macOS.
tool: animmix
order: 1
---

<!-- EXAMPLE DOC PAGE. Every file in content/docs/ needs a `tool:` field that
     matches the filename of a tool in content/tools/ — that's how they link. -->

## Requirements

- Maya 2022 or later
- No external Python packages

## Install

1. Download the latest release.
2. Unzip it into your Maya scripts folder:

```
Windows   C:\Users\<you>\Documents\maya\scripts\
macOS     ~/Library/Preferences/Autodesk/maya/scripts/
```

3. Restart Maya.

## Verify

Run this in the Script Editor. If it prints a version, you're set.

```python
import animmix
print(animmix.__version__)
```

## Troubleshooting

::note If Maya can't find the module, the folder is almost always one level too
deep. `animmix/__init__.py` must sit directly inside `scripts/`.
