---
title: Pendulum
category: foundational
summary: Overlap, drag and settle. The shortest route to understanding why things trail behind.
teaches: Overlap · drag · arcs
level: Second
image: /static/images/rigs/foundational/pendulum.png
download: /static/files/rigs/foundational/Pendulum.max
software: 3ds Max
order: 2
---

The pendulum is the ball's opposite. Where the ball travels through space with
no articulation, the pendulum articulates while going nowhere. Removing
translation is what makes this rig useful: with the base pinned, the only thing
capable of carrying the motion is the relationship between one segment and the
next, so overlap stops being a term and becomes visible.

## What it teaches

**Nothing in a connected chain moves at the same time.** Force enters at the
base and travels outward, which means each segment starts later than the one
before it and finishes later too. When every segment moves together the object
reads as a single rigid piece, regardless of how many joints it has.

**Drag is the lag, follow-through is the overshoot.** They are two halves of the
same behaviour and students routinely animate one without the other. A chain
that lags on the way out but stops dead at the end has been animated by
somebody thinking about drag as an effect rather than as physics.

**Arcs are not a style choice.** A pivoting object physically cannot travel in a
straight line. If the tip of the pendulum moves linearly, something in the rig
is being cheated.

## Exercises

1. **A single swing to rest.** Release from one side and let it settle. The whole exercise is in the decay.
2. **Move the pivot.** Translate the base and let the chain answer. This is where drag becomes obvious.
3. **A sharp stop.** Move the base quickly and halt it. Everything downstream should keep going and then return.
4. **Change the weight.** Animate the same swing as a heavy chain and as a light one, using only timing between segments.

## What to watch for

- **Offset your keys.** If the segments share keyframes, there is no overlap by definition. Each one should be a few frames behind its parent.
- **The tip travels furthest and arrives last.** It should also be the last thing to settle.
- **Settling is asymmetric.** The amplitude decays but so does the time between swings — the same rule as the ball, in rotation.
- **Do not stop everything on one frame.** Motion ends in sequence, base first.

## The most common failure

Uniform offset. Students discover overlap, apply the same three-frame delay to
every joint, and produce something that reads as a wave rather than a chain
reacting to force. The delay should vary with how far down the chain a segment
sits and how much resistance it has.

Next is [Ball and Tail](/rigs/foundational/ball-and-tail/), which puts this
chain onto a base that is moving.
