---
title: Combat Test
summary: Two weapon-based combat exercises investigating advanced body mechanics — aerial rotation, tempo control, and the problem of staying readable while airborne.
focus: Advanced body mechanics · aerial combat
software: 3ds Max
duration: 12 sec
video: https://drive.google.com/file/d/1pqrg9mfW9JTvZViPRxqqAwtgSGlvqdNQ/view
thumb: /static/images/personal/combat-test.jpg
order: 1
---

This was a study rather than a shot for anything. The question behind it was
narrow: how far can body mechanics be pushed once the character leaves the
ground, and what has to be true for the action to stay readable when it does?

Weapon-based combat is a useful vehicle for that question because it forces two
demands to compete. The body has to perform something physically committed, and
the weapon has to be legible as a separate object with its own path. Either
alone is manageable. Together they expose whatever is unresolved in the timing.

Two exercises were built, both centred on aerial acrobatics: a character
spinning in the air to release a thrown weapon, and a character lunging
downward with one.

## What being airborne actually constrains

The reason aerial work is a good test of mechanics is that it removes the
animator's easiest lie. On the ground, a character can be nudged into position
and the contact with the floor will quietly absorb the discrepancy. In the air
there is no floor to absorb anything. Once a figure leaves the ground its centre
of mass is committed to a path it cannot renegotiate, and everything the
character does afterwards has to happen *around* that path rather than in spite
of it.

What remains available is rotation and shape. A tucked body rotates faster, an
extended one slower, and the exchange between the two is the only honest way to
control the speed of a spin mid-flight. Working within that constraint rather
than around it is what separates aerial animation that reads as physical from
aerial animation that reads as floating.

## Exercise one — the shinobi

The first exercise was a female shinobi performing an airborne spin and
releasing a thrown weapon out of the rotation.

The spin was the hardest part, and specifically its **tempo**. A rotation that
is uniformly fast becomes a smear the audience cannot parse; one that is
uniformly slow drains the force out of the action. The solution is uneven —
accelerate into the rotation, hold a legible attitude at the point where the
information matters, then carry through. Getting that unevenness to feel like
physics rather than like an animator hitting the brakes took the most iteration
of anything in the study.

Layered on top was a staging problem. At the moment of release, two things need
to be seen at once: the character, and the weapon leaving the hand. They compete
for the same instant and the same region of screen. If the body is favoured, the
throw reads as a gesture with no object; if the weapon is favoured, the throw
loses its author. Resolving it meant treating the release as the beat the whole
rotation is arranged around, rather than an event that happens somewhere inside
it.

## Cloth and hair as consequences

The character's costume and long hair produced the other significant problem,
and it is worth separating it from the first because the failure mode is
different.

Secondary motion is often treated as decoration added at the end. It isn't. It
is **evidence** — the audience reads cloth and hair as proof that the body moved
the way the animation claims it did. When secondary motion contradicts the
primary action, the contradiction is what gets believed.

Long hair is particularly unforgiving here. Its length gives it a slow response;
it lags further behind the head than short hair and settles later, and if it is
driven too tightly it stops reading as hair and starts reading as wire. Driven
too loosely, it becomes noise that competes with the silhouette at exactly the
moment the silhouette is doing the most work. The cloth carried a related but
blunter constraint: it had to move enough to confirm the motion while never
intersecting the body, since a single frame of clipping undoes the illusion
entirely.

## Exercise two — the male ninja, and what didn't work

The second exercise followed a similar shape with a different emphasis: a fast
launch, a deliberate suspension at the apex, a spin, then a landing and
recovery.

The tempo change was the point of the exercise. The launch is quick, the
suspension is long, and the contrast between the two is what sells the height.
This is one of the few places where exaggeration is not really exaggeration —
vertical velocity genuinely approaches zero at the top of a jump, so the
character does linger there. Holding that moment is amplifying something real
rather than inventing it.

**The recovery is where this one falls short.** The landing itself is fine; what
follows it is stiff. The character arrives, and then stops, rather than arriving
and continuing to resolve. This matters more than it might appear, because the
settle is where weight is finally proved. Force absorbed through bending joints
is the audience's evidence that the body has mass; a figure that lands and
immediately holds still reads as weightless retroactively, undoing the
suspension that preceded it.

The correction is not more keys on the landing frame. It is allowing the body to
keep travelling after contact — the mass continuing down through the support,
the spine and head arriving late, a small opposing motion as the character
recovers their balance rather than simply having it. That is the specific thing
this exercise taught, and it was worth the shot not being successful to learn it.

## The camera as a participant

The camera was treated as part of the mechanics rather than as a window onto
them. It shakes on impact and pulls back when both characters commit to an
attack.

Both choices are doing work. Shake is a proxy for force the body alone cannot
communicate — it transfers the impact to the viewer's frame of reference, which
is why it reads as weight rather than as an effect. Pulling back at the moment
of maximum action serves the opposite need: fast, large movement requires room,
and a camera that stays tight during it crops exactly the silhouette the
audience is relying on to follow what is happening.

## What the study produced

The useful outcome was not the shots. It was a clearer sense of where aerial
combat animation actually fails: not in the spectacular middle, which tends to
get the most attention, but at the two joins either side of it — the commitment
into the air, and the resolution out of it. The airborne section is constrained
enough that physics does much of the work. The landing is where the animator has
to supply everything, and it is where this study came up short.
