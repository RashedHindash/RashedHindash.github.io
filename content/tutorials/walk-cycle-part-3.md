---
title: Walk Cycle (Part 3)
category: foundation
summary: The polish pass. Refining the feet and the poses, then cleaning the animation up properly in the Curve Editor.
teaches: Polish · foot refinement · curve editor cleanup
level: Ninth
video: https://drive.google.com/file/d/1o-c9LLkehP6DM18Jbxw1v0PUXVmgRkVH/view
thumb: /static/images/tutorials/thumbs/walk-cycle-part-3.jpg
software: 3ds Max
order: 9
---

The last part is the one most people skip, and it is the difference between an
animation that works and one that looks finished. Nothing new is added here.
Everything already present gets refined.

## What the video covers

Polishing the feet, tightening the poses, and then working in the Curve Editor:
finding the places where the interpolation is doing something the poses did not
ask for, and correcting it so the motion is clean throughout.

## Why the polish pass is its own video

**The Curve Editor is where hidden problems live.** A pose can be correct on
every key and still produce bad motion between them, because the curves are
overshooting, flattening in the wrong place, or introducing movement on an axis
nobody touched. None of this is visible in the viewport until you look for it.

**Feet are where the eye goes to check honesty.** Slipping contacts, a heel that
does not roll, a toe that breaks through the floor. These are small, and they are
the errors that make an otherwise good walk feel cheap.

**Polish is diagnosis, not decoration.** The work is finding what is wrong rather
than adding what is missing. If a pass adds new ideas, the earlier stages were
not finished.

## What to watch for

- **Flat tangents where you wanted a hold, and only there.** A flat curve in the middle of a moving section stalls the motion.
- **Unintended channels.** Check axes you never deliberately animated for stray movement.
- **Cycle seams.** The last frame has to hand over cleanly to the first. Curves that do not match at the loop point produce a hitch once per stride.
- **Watch it at speed, repeatedly.** Polish problems are almost invisible frame by frame and obvious in motion.

That completes the foundation series. The [foundational
rigs](/rigs/foundational/) cover the same ground as practice exercises.
