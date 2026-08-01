---
title: Getting started
summary: The naming convention Animmix expects, and the snapshot workflow everything else is built on.
tool: animmix
order: 2
---

## Set your rig up first

Animmix identifies the left and right sides of a character from **controller
names**. Controllers must include `_L` and `_R` so the system can tell the two
sides apart during operations like mirroring.

```
ctrl_arm_L      ✓
ctrl_arm_R      ✓
ctrl_arm_left   ✗ Animmix won't pair this
```

This gets checked automatically by the **Setup Check**, which runs before the
pose-based tools and confirms the rig follows the expected structure. If the
check fails, fix the naming rather than working around it, because the pose tools
depend on it.

## Rig types

| Rig type | Supported |
| --- | --- |
| Standard bone-based | Yes |
| Custom rig setups | Yes |
| CAT | Not yet |
| Biped | Not yet |

CAT and Biped use internal animation systems that need specialised handling.
They're planned once the core feature set is stable.

## The snapshot workflow

Everything in Animmix is built on snapshots. The basic loop:

1. **Select** all the animation controllers for the character.
2. Click **Snapshot Tool** in the interface.
3. Give the snapshot a **clear, descriptive name**. You'll be picking it out of a list later.
4. **Save** it.

The snapshot stores the current pose state so you can recall, compare against,
or restore it later.

## Why bother

Two reasons, and the second is the one that matters most.

**It's non-destructive.** You can push a pose much harder when you know the
previous state is one click away. That tends to produce bolder posing than
working without a safety net.

**The other tools depend on it.** The rest of Animmix operates against saved
pose states rather than editing blind, so taking snapshots isn't housekeeping. It's what makes the rest of the toolkit work correctly.

::note Name snapshots as if someone else will read them. `contact_L_pass_02`
survives a week away from the file. `test3` does not.
