---
title: Tutorial title — what the viewer will be able to do afterwards
summary: One line promising a specific outcome, not a topic.
date: 2026-04-22
software: Maya
level: Intermediate
duration: 18 min
files: https://drive.google.com/drive/folders/REPLACE_WITH_FOLDER_ID
tags: [maya, rigging]
video: https://drive.google.com/file/d/REPLACE_WITH_YOUR_FILE_ID/view
cover:
---

<!-- EXAMPLE FILE. Copy it for each tutorial, or delete it. -->

Say who this is for and what they need before starting. One short paragraph.

## Before you start

- Maya 2024 or later
- The scene files linked in the metadata above
- Roughly twenty minutes

## Chapters

Timestamps make a long video usable, and they take two minutes to write.

| Time | Section |
| --- | --- |
| 00:00 | Setup and scene tour |
| 03:40 | Building the control |
| 11:05 | Connecting the constraint |
| 15:20 | Testing the range |

## Notes

Anything that was hard to say on camera, corrections, or the thing you forgot
to mention. This is also where people paste the code from the video:

```python
import maya.cmds as cmds

cmds.circle(name="ctrl_wrist_L", normal=(1, 0, 0), radius=2.4)
```
