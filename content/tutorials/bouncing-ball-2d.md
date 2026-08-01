---
title: Bouncing Ball (2D)
category: foundation
summary: The first exercise. A shape, a timeline, and the smallest possible introduction to keys, timing, and squash and stretch.
teaches: Timeline · keys · timing · squash and stretch
level: Start here
video: https://drive.google.com/file/d/1LRhOpNiP-c6Pa-1AQ_vXRdXFXfh5YwZl/view
thumb: /static/images/tutorials/thumbs/bouncing-ball-2d.jpg
software: 3ds Max
order: 1
---

This one starts in two dimensions on purpose. Before anything else has to be
managed, the only variables are a shape, where it is, and when it is there.
Everything that follows in the series is a more complicated version of that
sentence.

## What the video covers

We take a simple shape and move it across the screen, which is enough to
introduce the pieces of the software you cannot avoid: the timeline, what a key
actually is, and how the gap between two keys becomes motion. Then we bounce the
ball on the spot, and squash and stretch enters as a consequence of the speed it
is already travelling at.

## Why start here

**Two dimensions removes the decisions you are not ready to make.** There is no
camera to place, no depth to judge, no rig to interpret. A student working flat
who cannot get a bounce to read knows the problem is timing, because timing is
all there is.

**Keys are positions in time, not just positions.** The most common early
misunderstanding is treating keys as poses to be placed and the software as the
thing that connects them. The connection is the animation. Where you put the
keys determines what happens between them, and that relationship is easier to
feel with one shape than with a character.

**Squash and stretch is caused, not applied.** The ball deforms because it is
moving fast, or because it just hit something. Introducing it here, attached to
a bounce that already works, establishes it as a consequence rather than a
decoration added later.

## What to watch for

- **Contact is the extreme.** The most squashed frame is the frame of impact, and it is usually a single frame.
- **The apex is slow.** The ball spends more frames near the top than anywhere else, and moves the least while it is there.
- **Deformation returns to neutral.** Between the fast frames the ball should be close to a circle again.
- **Decay in both directions.** As the bounce loses height it should also lose the time between bounces.

Next in the series is [Bouncing Ball (3D)](/tutorials/foundation/bouncing-ball-3d/),
which is the same exercise rebuilt inside 3ds Max.
