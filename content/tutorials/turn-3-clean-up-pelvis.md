---
title: Clean Up the Pelvis in the Curve Editor
category: body-mechanics
series: Turn
series_order: 1
summary: Polishing the pelvis and hips properly, in position and orientation, so the lower body is finished before the upper body starts.
teaches: Curve editor · pelvis and hip polish · position and orientation
level: Intermediate
video: https://drive.google.com/file/d/1jQ6Ya8hkUnPbiCCf6y70EVfFY9TB6ghR/view
thumb: /static/images/tutorials/thumbs/turn-3-clean-up-pelvis.jpg
software: 3ds Max
order: 3
---

Retiming got the beats right. This video makes the motion between those beats
clean, working on the pelvis and hip controls in both position and orientation.

## What the video covers

Polishing the pelvis and hips: their translation and their rotation, taken into
the Curve Editor and worked until the curves describe what the poses intended.
The goal is a lower body finished to the point where the upper body can be built
on top of it without needing to come back.

## Why finish the lower body first

**The upper body is a response.** Chest, arms and head answer what the hips
already did. Building them on a pelvis that is still moving is the same mistake
as polishing before retiming, one stage further along.

**Curves hold problems that poses do not.** A pelvis can be correct on every key
and still drift, overshoot, or stall between them. None of that appears in the
viewport until you look at the curves, and all of it reads as wrongness at
speed.

**Position and orientation fail differently.** Translation errors read as
floating or sliding. Rotation errors read as the body being steered rather than
turning. They need checking separately because they are easy to confuse when
watching the result.

## What to watch for

- **Overshoot you did not ask for.** Default tangents will happily send a control past its key and back.
- **Flat spots mid-motion.** A flat tangent in the middle of a move stalls it. Flat where you wanted a hold, and only there.
- **Stray channels.** Check axes you never deliberately touched.
- **Rotation order artefacts.** A curve that suddenly jumps by a large value is usually a rotation representation problem rather than an animation problem.

Next: [Clean Up the Spine and
Arms](/tutorials/body-mechanics/turn-4-clean-up-spine-and-arms/).
