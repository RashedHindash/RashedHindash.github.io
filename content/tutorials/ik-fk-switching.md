---
title: IK / FK Switching
category: animation-tips
summary: What IK and FK actually are, when each one is the right answer, and the correct workflow for switching between them without leaving a pop behind.
teaches: IK and FK · switching workflow · pose matching
level: Intermediate
video: https://drive.google.com/file/d/1IttLDPRpS-_g1ktCuLsfNFtLQ6zpYu8j/view
thumb: /static/images/tutorials/thumbs/ik-fk-switching.jpg
software: 3ds Max
order: 1
---

Almost every rig offers both, almost every shot needs both, and switching
between them is where a lot of otherwise good animation quietly breaks.

## What the video covers

The concept behind IK and FK, the process of switching from one to the other and
back, and the workflow that makes those switches invisible.

## The two systems

**FK drives a limb from its root.** Rotate the shoulder and the whole arm
follows. The hand goes wherever the chain sends it, which means it arcs
naturally, because that is what a chain rotating about a joint does.

**IK drives a limb from its end.** Place the hand and the rig solves the elbow
and shoulder to reach it. The hand goes exactly where you put it and stays
there, regardless of what the body does.

Neither is better. They answer different questions, and the question is always
the same one: **does this hand or foot need to stay in a fixed place in the
world?**

- **Yes:** IK. A planted foot, a hand on a prop, a palm against a wall, anything carrying weight.
- **No:** FK. A swinging arm, a throw, a gesture, anything being carried by the body.

The most common symptom of choosing wrong is a hand that slides when it should
be locked, or an arm that feels dragged rather than swung.

## Why switching causes pops

The two systems describe the same limb in different terms. When you switch, the
rig stops taking direction from one set of controls and starts taking it from
the other, and unless both describe the same pose at that instant, the limb
jumps to whatever the incoming controls happen to be set to.

That jump is a single frame, which is exactly the kind of error that is
invisible while scrubbing and obvious at speed.

## The workflow

1. **Decide where the switch happens** before you touch anything. It should land on a frame where the limb is doing least, not in the middle of an action.
2. **Match the pose across the switch.** The incoming controls have to be placed so they describe the same limb position the outgoing ones were producing. Most rigs offer a match or snap function for exactly this.
3. **Key both sides on the switch frame.** The outgoing system needs a key holding its final value, and the incoming one needs a key at its matched value.
4. **Key the blend value itself,** so the changeover happens where you intended and not gradually across the shot.
5. **Play it at speed and watch the hand.** If there is a pop, it will be at the switch frame, and it is almost always a matching problem rather than a rig problem.

## What to watch for

- **Switch on a quiet frame.** A changeover during a fast action is far harder to hide than one during a hold.
- **Check the elbow, not just the hand.** IK solves the elbow for you, and the solution it picks may not be the one FK was producing. A matched hand with a flipped elbow is still a pop.
- **Do not blend slowly to hide a bad match.** A gradual transition turns a one frame pop into a slow drift, which reads as the arm melting.
- **Watch for it on the feet too.** The same problem exists on legs and is more damaging there, because the floor makes any slip obvious.
