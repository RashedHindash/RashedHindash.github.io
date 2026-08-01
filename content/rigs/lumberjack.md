---
title: Lumberjack
category: body-mechanics
summary: An advanced production-style rig: IK/FK on the limbs and spine, bendy limbs, squash and stretch, and roll, bank, tilt and twist controls throughout.
teaches: Advanced rig control · full body mechanics
level: Advanced
image: /static/images/rigs/body-mechanics/lumberjack.png
download: /static/files/rigs/body-mechanics/Lumberjack.max
software: 3ds Max
order: 1
---

The Lumberjack is a considerable step up from the mannequin. Where that rig
gives you a body and asks you to move it, this one gives you the kind of control
set you would expect on a production character, and with it the corresponding
responsibility to know which control you actually want.

## What the rig offers

- **IK and FK on the limbs**, switchable, so an arm can be planted against the world or carried by the shoulder depending on what the shot needs
- **A full IK/FK spine**, which makes the torso steerable rather than merely posable
- **Bendy limbs**, allowing curvature through the length of an arm or leg instead of a straight segment between two joints
- **Squash and stretch controllers**, so proportion can be pushed for impact or reach
- **Roll, bank, tilt and twist controls** distributed through the rig, giving fine articulation at the feet, the spine and the extremities

That is a lot of surface area. Used well it removes almost every technical
obstacle between an idea and the screen. Used carelessly it produces animation
that is technically elaborate and physically incoherent, which is a harder
problem to diagnose than a stiff pose.

## What it teaches

**IK and FK are answers to different questions, not preferences.** Use IK when
something must stay put in the world: a hand on an axe handle, a foot planted on
the ground, a palm pressed against a surface. Use FK when a limb is being
carried by the body and should arc naturally from its parent, as in a swing or a
throw. Choosing wrong is why so many otherwise good shots have hands that slide
or arms that feel like they are being dragged.

**A spine you can steer is a spine you can overuse.** Full IK/FK through the
torso means the chest and hips can be counter-rotated independently, which is
exactly what contrapposto requires. It also means it is trivially easy to
produce a body shape no spine could actually hold. Push it, then check the pose
against something a person could stand in.

**Bendy limbs are for arcs, not for hiding straight lines.** Curvature through a
limb should be the consequence of force travelling along it, following the same
logic as the [Pendulum](/rigs/foundational/pendulum/). When it becomes a way to
make any pose look smooth, the rig has started animating instead of you.

**Squash and stretch on a character follows the same rule as on the ball.** It
belongs at the extremes of speed and at contact, and volume still has to survive.
The scale of it should be far smaller here than instinct suggests, because a
figure that reads as a body invites the audience to notice when it stops
behaving like one.

## Exercises

1. **A weighted lift.** An axe, a log, anything with mass. Where is the load, and which joints are absorbing it?
2. **A swing with an IK/FK switch.** Plant the hands in IK during the wind-up, release to FK through the strike, and get the transition to disappear.
3. **A jump with a full landing.** Anticipation, launch, suspension, contact, and a settle that keeps resolving after the feet arrive.
4. **A weight shift with the spine only.** Feet planted, no steps. Move the mass using hips, chest and head, nothing else.

## What to watch for

- **The IK/FK transition.** Switching mid-shot is normal; a visible pop at the switch frame is not. Match the pose across the change before you move on.
- **Foot roll and bank.** These exist to keep contact convincing through a step. A foot that stays flat through a heel-to-toe roll reads as a plank.
- **Twist distribution.** A forearm that twists entirely at the wrist looks broken. Spread rotation along the available controls.
- **Over-articulation.** If a pose needed six controls to construct, check whether one clear line of action would have done more work than all six.

## The most common failure

Solving with controls rather than with mechanics. The rig is capable enough that
almost any problem can be forced into looking acceptable on the frame you are
sitting on, and the result is animation that survives frame-by-frame inspection
and collapses in motion. When something is not reading, the first question is
still where the weight is and what shape the body is making, not which
additional controller might fix it.
