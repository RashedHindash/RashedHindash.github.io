---
title: Ball and Tail
category: foundational
summary: A bouncing ball with a chain of tail controls: overlap and follow-through on top of solid timing.
teaches: Follow-through · overlapping action
level: Third
image: /static/images/rigs/foundational/ball-and-tail.png
download: /static/files/rigs/foundational/Ball_and_Tail.max
software: 3ds Max
order: 3
---

This is the first rig in the set that asks two things to disagree with each
other on purpose. The ball has a job, which is to bounce convincingly, and the tail has a
different one: react to what the ball just did, a few frames later than it did
it.

It combines the previous two exercises, and that combination is where most
students discover their bouncing ball was not as solid as they thought. A tail
is unforgiving: it exposes whether the ball's timing was genuinely motivated or
merely plausible in isolation.

## What it teaches

**Secondary motion is driven, not authored.** The tail does not have its own
performance. Everything it does should be traceable to a force the ball applied
to it. When a tail starts doing something interesting on its own, it stops
reading as attached.

**Force arrives late and leaves late.** At the moment the ball changes
direction, the tail is still travelling the old way. It reverses only after the
ball has committed, which is what produces the whip.

**The settle is the tell.** When the ball comes to rest, the tail carries on for
a beat and then resolves. A tail that stops on the same frame as the ball
removes all the weight the bounce just established.

## Exercises

1. **Bounce and settle with the tail switched off in your head.** Animate the ball first and do not touch the tail until it works.
2. **Add the tail with offsets only.** No new ideas. The tail simply follows what is already there, late.
3. **A hard direction change.** Send the ball one way, reverse it sharply, and let the tail whip.
4. **A heavy tail and a light tail** over the identical ball animation.

## What to watch for

- **Never key the tail on the ball's keyframes.** If they share frames, the tail is welded rather than attached.
- **Watch the tip.** It should describe a smooth arc even when the base is doing something abrupt.
- **Contact frames.** The tail should still be arriving when the ball has already left the ground.
- **Overlap within the tail itself.** It is a chain, so the same rules as the [Pendulum](/rigs/foundational/pendulum/) apply along its length.

## The most common failure

Animating the tail as decoration, adding a pleasing wave that has no
relationship to the ball's timing. It looks fine in isolation and falls apart
the moment anyone watches the two together, because the eye is extremely good
at spotting a consequence that does not match its cause.

Next: [Ball and Legs](/rigs/foundational/ball-and-legs/), where the ground
starts pushing back.
