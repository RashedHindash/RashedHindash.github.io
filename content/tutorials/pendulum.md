---
title: Pendulum
category: foundation
summary: A platform with a rope hanging from it. The first exercise where one part of an object has to answer to another.
teaches: Overlapping action · drag · arcs
level: Third
video: https://drive.google.com/file/d/1N71LLWPJ_RngWKiq5sN2GdrYr-PQSJ3g/view
thumb: /static/images/tutorials/thumbs/pendulum.jpg
software: 3ds Max
order: 3
---

Everything so far has moved as a single piece. This is where that stops. We
build a platform with a rope dangling from it and animate the platform, letting
the rope work out its own answer a few frames later.

## What the video covers

Setting up the platform and the hanging rope, then animating the base and
working down the chain so the rope follows rather than travels with it. The
whole exercise is about the delay between one segment and the next, and what
happens at the end of a motion when the base has stopped and the rope has not.

## Why this exercise exists

**Overlapping action is invisible until you remove translation.** In a bouncing
ball, timing carries everything. Here the base can move very simply and the
interest comes entirely from how the rope responds. That isolation is what makes
the principle land.

**Force travels along a chain, it does not arrive everywhere at once.** The
segment nearest the platform moves first, the tip moves last, and each one
starts later than its parent. When every segment shares keyframes the object
reads as one rigid piece regardless of how many joints it has.

**Stopping is where the exercise is won.** Anyone can make a rope swing. Making
it settle, with the amplitude decaying and the gaps between swings shortening,
is the part that separates a rope from a windscreen wiper.

## What to watch for

- **Offset the keys.** Shared keyframes mean no overlap, by definition.
- **The tip arrives last and settles last.** It travels furthest, so it has the most to resolve.
- **Vary the offset.** A uniform delay on every joint reads as a wave rather than a chain reacting to force.
- **Arcs.** A pivoting object cannot travel in a straight line. If the tip goes linear, something is being cheated.

Next: [Hammer Strike](/tutorials/foundation/hammer-strike/), where in-betweens
enter the picture.
