---
title: Animmix
summary: A modern animation workflow toolkit for 3ds Max 2026+. Snapshot-based pose tools for character animation, with support for complex rigs.
status: In development
version: 1.2
language: 3ds Max 2026+
repo: https://github.com/RashedHindash/ANIMMIX
download:
date: 2026-02-23
tags: [3ds-max, animation, tools]
cover: /static/images/tools/animmix/logo.png
order: 1
---

**Animate your way.**

Animmix is an animation workflow toolkit for 3ds Max 2026 and later. It brings
the kind of animation tooling Maya users take for granted into Max: pose
snapshots, mirroring, and non-destructive pose work, built for character
animation on complex rigs.

## Get it

The tool lives on GitHub. Download it from there, along with every previous
release:

- **[github.com/RashedHindash/ANIMMIX](https://github.com/RashedHindash/ANIMMIX)**, the repository
- **[Releases](https://github.com/RashedHindash/ANIMMIX/releases)**, where 1.2 is current

Installation takes about a minute. See [Installation](/tools/animmix/animmix-installation/).

## The interface

::image /static/images/tools/animmix/interface.png | The Animmix panel in 3ds Max

The panel is organised into four working groups:

- **Tween / Blend / Default**, with an intensity slider and an overshoot toggle
- **Tangents**: Cycle, Guess, Polish, Flow, Bounce, Native
- **Pose**: Copy, Paste, Mirror, Reset, Snapshot, Select Opposite, Selection Sets
- **Keys**: Hammer, Smart Key, Delete, and nudge controls

Auto-recovery runs underneath, with a history you can step back through.

## How it works

Animmix is built around **snapshots**. You select your animation controllers,
take a named snapshot of the current pose, and that stored state becomes
something you can recall, compare against, or restore later.

That matters for two reasons. It means pose work is non-destructive, so you can
push a pose hard knowing the previous state is retrievable, and it's what the
rest of the tools build on, since they operate against saved pose states rather
than editing blind.

## What it supports today

Animmix is a work in progress and is still evolving through iterative testing.

- **Supported**: standard bone-based rigs, and custom rig setups
- **Not yet supported**: CAT and Biped rigs

CAT and Biped rely on internal animation systems that need specialised
handling. Support is planned for a future release, once the core feature set
is finalised and stable.

::note The rig must use `_L` and `_R` in controller names for mirroring to
work. Animmix validates this during its Setup Check. See
[Getting started](/tools/animmix/animmix-getting-started/).
