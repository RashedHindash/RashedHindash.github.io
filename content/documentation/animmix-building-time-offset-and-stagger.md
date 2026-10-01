---
title: Animmix: Building Time Offset and Stagger
summary: How the Offset mode in Animmix slides animation through time and staggers a hierarchy into follow-through, the four versions it took to get there, and what still does not work.
date: 2026-10-01 22:30
tags: [animmix, tools, 3ds max, python, development]
---

At the end of [the Tween Machine post](/documentation/animmix-building-the-tween-machine/),
I said the next one would be about Time Offset and Stagger. This mode took me
more attempts than I expected. I rewrote it several times, and while writing this
post I found problems I did not know were there. This post covers how it works and
how it got here, and ends with what still does not work.

Like the last one, it is a technical post with a lot of code in it. All the code
here comes from the current version of Animmix for 3ds Max 2026 and later.

## Why I wanted it

Overlap and follow-through are some of the first things you learn as an animator.
A tail, an arm or an antenna should not move at exactly the same time as the body
it is attached to. It drags a few frames behind, and that delay is a big part of
what makes the motion look natural.

In 3ds Max, getting that delay usually means going into the Dope Sheet and sliding
keys by hand, object by object. If the animation is a cycle, you also have to fix
the loop afterwards, because the keys you pushed past the end no longer line up
with the start. It works, but it is slow, and it is hard to try a few different
amounts and compare them.

I wanted it on the same slider as everything else. Pick the objects, drag, watch
the motion slide through time, and let go when it looks right. For a chain, the
pieces further down should trail behind the ones above them, without me having to
offset each one separately.

## What it does

Offset lives in the menu on the Tween button, next to Tween and Space. When you
pick it, the slider turns orange.

The keys do not move. Each key stays on its frame and takes the value the curve
had a few frames away. Dragging right makes the motion happen earlier, and
dragging left makes it happen later.

The motion also wraps around inside its range. Whatever slides off one end comes
back in at the other, so a looping animation still loops while you drag.

If you select a hierarchy, Offset staggers it. The objects further down the chain
trail behind the ones above them, so one drag gives you follow-through on the
whole chain.

## How it got here

Offset went through four versions to get where it is now: two experiments in
December, a rewrite for 1.1 that set the approach it still uses, and a March update
that made it follow the keys you have selected. Going back through my old files
for this post was a good reminder of how many wrong turns it took.

### December 2025: two ideas at once

My first attempts were two separate approaches to the same problem, written side
by side.

The first one, which I called Dense Temporary Keys, added a key on every frame
while you dragged and set each one from the original curve. When you let go, it
kept the original keys plus any peaks and valleys it found, and deleted the rest.

The second, Wave Riding, did not add keys at all. It sampled the curve every tenth
of a frame, recording both the value and the slope, and then rewrote only the
selected keys with values from elsewhere along the curve. The first and last keys
were given custom tangents set from the curve's slope at that point, and the keys
in between were left to Max's smooth tangents. The offset was fixed at up to 20 frames either way.

Both of them were trying to solve the same problem: keeping the full height of the
motion after it moved. I even wrote a small test for it. It animated a point from 0
up to 100, down to -100 and back, offset it by four different amounts, and measured
whether the swing still covered all 200 units. Wave Riding was the one that went
out in the first public release, on 31 December 2025.

### February 2026: bake, offset, rebuild

For version 1.1 I threw that away and rewrote Offset around a different idea,
which is still the one it uses today:

1. When you press the slider, bake the curve down to a key on every frame.
2. While you drag, set every one of those keys from the original curve, a few
   frames earlier or later.
3. When you let go, rebuild the curve back down to the original keys.

Two other things changed in the same rewrite. The offset was no longer a fixed
number of frames. It became a share of each curve's own length, so a long motion
and a short one respond to the slider in proportion. And the hierarchy stagger was
added.

Version 1.2, a few weeks later, only added some memory clean-up to this part.

### March 2026: following the selection

The last big change made Offset follow the keys you have selected. In 1.1 and 1.2,
every key on a curve had to be selected or the curve was skipped. From March, if
you select some keys, Offset works only between the first and last of them. If
you select none, it works on the whole curve. That version also started releasing
its references to the scene properly, and paused Animmix's crash recovery
snapshots while an offset is being dragged.

That March rewrite also broke something, which I only found while writing this
post. I cover it in the last section.

## Building the hierarchy order

When the slider is pressed, the first job is to work out where each selected
object sits in its hierarchy. The depth is just the number of parents above it:

```python
def _get_hierarchy_depth(obj):
    """Get the depth of an object in the hierarchy (0 = root)."""
    depth = 0
    current = obj
    while current.parent is not None:
        depth += 1
        current = current.parent
    return depth
```

The objects are then sorted by that depth, parents first, and each one gets a
stagger factor between 0 and 1:

```python
def _sort_by_hierarchy(objects):
    obj_depths = []
    for obj in objects:
        depth = _get_hierarchy_depth(obj)
        obj_depths.append((obj, depth))

    # Sort by depth (parents first, then children)
    obj_depths.sort(key=lambda x: x[1])

    # Assign stagger index (0 = shallowest/parent, higher = deeper/children)
    result = []
    for i, (obj, depth) in enumerate(obj_depths):
        result.append({
            'obj': obj,
            'depth': depth,
            'stagger_index': i,
            'stagger_factor': i / max(1, len(obj_depths) - 1) if len(obj_depths) > 1 else 0
        })

    return result
```

The top of the chain gets 0 and the bottom gets 1, with everything else spread
evenly in between. One detail to be aware of: the factor comes from each object's
position in the sorted list, not from its depth. Two siblings at the same depth
still get different factors, one after the other.

## Choosing the range

Each animated track is handled on its own. Position, rotation and scale tracks
with separate X, Y and Z sub-tracks are split into those sub-tracks, which are
resolved through any list controllers, exactly like in the Tween Machine.

For each track, Offset first decides which part of the curve it is going to work
on:

```python
if has_selected:
    if all_selected:
        # ALL keys selected -> use full key range
        first_time = int(all_key_times[0])
        last_time = int(all_key_times[-1])
    else:
        # SOME keys selected -> use selected range only
        first_time = int(selected_key_times[0])
        last_time = int(selected_key_times[-1])
elif has_keys:
    # NO keys selected -> use full key range
    first_time = int(all_key_times[0])
    last_time = int(all_key_times[-1])
else:
    # NO keys at all -> use timeline range
    first_time = int(rt.animationRange.start)
    last_time = int(rt.animationRange.end)
```

If at least two keys are selected, it works between the first and last of them.
Otherwise it uses the whole span of the curve's keys. If the track has fewer than
two keys, it falls back to the timeline.

## Sampling and baking

Before anything changes, the original curve is recorded, one value per frame:

```python
original_curve = {}
pad = min(time_range, 500)
for frame in range(first_time - pad, last_time + pad + 1):
    try:
        with pymxs.attime(frame):
            original_curve[frame] = float(ctrl.value)
    except:
        pass
```

This is the reference for the whole drag. Every update reads from this untouched
copy, never from the keys that are being changed, so dragging back and forth never
builds up errors.

Then comes the bake. A key can only hold a value on its own frame. To slide the
motion through time, every frame needs a key of its own, so that each one can take
a value from somewhere else on the curve:

```python
existing_key_frames = set(int(t) for t in all_key_times)

with pymxs.animate(True):
    for frame in range(first_time, last_time + 1):
        if frame in existing_key_frames:
            continue

        try:
            val = original_curve.get(frame, 0)
            rt.addNewKey(ctrl, frame)
            idx = rt.getKeyIndex(ctrl, frame)
            if idx > 0:
                key = rt.getKey(ctrl, idx)
                key.value = val
                key.inTangentType = rt.Name("linear")
                key.outTangentType = rt.Name("linear")
        except:
            pass
```

The new keys get the curve's own value on their frame, so the bake on its own does
not change the motion. It just gives the next step something to work with. The
original keys are left as they are, and their times and tangent lengths are stored
for the rebuild later.

## Sliding the motion

`apply_time_offset()` runs every time the slider moves. It works out how many
frames each track should shift, then sets every key from the original curve at
that distance:

```python
# Base offset + staggered amount
# The stagger adds additional offset based on hierarchy position
base_offset = amount * time_range
stagger_offset = abs(amount) * time_range * stagger_multiplier * 0.5  # 0.5 = stagger strength

if amount >= 0:
    frame_offset = base_offset * (1 - stagger_factor) + stagger_offset
else:
    frame_offset = base_offset * stagger_factor - stagger_offset

num_keys = rt.numKeys(ctrl)
for k_idx in range(1, num_keys + 1):
    try:
        key = rt.getKey(ctrl, k_idx)
        key_time = float(key.time)

        sample_time = key_time + frame_offset

        # Wrap for looping
        while sample_time < first_time:
            sample_time += time_range
        while sample_time > last_time:
            sample_time -= time_range

        # Interpolate value
        frame_low = int(sample_time)
        frame_high = frame_low + 1
        frac = sample_time - frame_low

        val_low = original_curve.get(frame_low, original_curve.get(first_time, 0))
        val_high = original_curve.get(frame_high, original_curve.get(last_time, 0))

        new_value = val_low + (val_high - val_low) * frac
        key.value = new_value
        count += 1
    except:
        pass
```

`amount` is the slider value divided by 100, and `time_range` is the length of the
track's working range in frames. `stagger_multiplier` is the object's stagger
factor when you drag right, and one minus it when you drag left.

Each key looks up the original curve `frame_offset` frames away. If that lands
outside the range, it wraps around to the other end, which is what keeps a cycle
looping. The offset is rarely a whole number of frames, so the value is blended
between the two frames on either side, the same lerp as in the Tween Machine.

### What the stagger actually does

If you work through the code, it simplifies to two lines. With `a` as the slider
amount, `R` as the range and `s` as the stagger factor:

```python
# Dragging right (a >= 0)
frame_offset = a * R * (1 - s / 2)

# Dragging left (a < 0)
frame_offset = a * R * (1 + s) / 2
```

A positive offset means each key reads from later in the curve, so the motion
happens earlier. Here is what that gives for three objects in a chain, on a
24-frame range:

| Object | Stagger factor | +50% | -50% |
|---|---|---|---|
| Parent | 0 | 12 frames earlier | 6 frames later |
| Middle | 0.5 | 9 frames earlier | 9 frames later |
| Child | 1 | 6 frames earlier | 12 frames later |

In both directions the child ends up 6 frames behind the parent. Dragging right or
left decides whether the whole chain moves earlier or later, and the children
always trail. That is the follow-through I wanted.

I checked this in Max with a chain of four objects, each swinging from 0 to 90
degrees and back over 24 frames. While the slider was held, at +25% they moved 6,
5, 4 and 3 frames earlier, and at -25% they moved 3, 4, 5 and 6 frames later,
exactly what the formula predicts. Two of the four were siblings at the same depth,
and they still came out a frame apart, because of the sorting detail above. Letting
go is another story, and I come back to that at the end.

## Letting go: rebuilding the curve

While you drag, the track has a key on every frame. That is fine for a preview, but
nobody wants to keep animating on a curve like that. So when you let go,
`clear_offset_cache()` rebuilds the curve back down to the original keys.

First it reads the offset curve at each original key time, along with its slope,
by looking half a frame either side:

```python
for t in sorted_times:
    with pymxs.attime(t):
        val = float(ctrl.value)
    with pymxs.attime(t - epsilon):
        val_before = float(ctrl.value)
    with pymxs.attime(t + epsilon):
        val_after = float(ctrl.value)

    slope = (val_after - val_before) / (2 * epsilon)
    final_data[t] = {'value': val, 'slope': slope}
```

Then it deletes every key on the track and adds back only the original ones, each
with that value and a custom tangent built from the slope:

```python
while rt.numKeys(ctrl) > 0:
    rt.deleteKey(ctrl, 1)

with pymxs.animate(True):
    for i, t in enumerate(sorted_times):
        rt.addNewKey(ctrl, t)
        ...
        key.value = data['value']
        key.inTangentType = rt.Name("custom")
        key.outTangentType = rt.Name("custom")
        ...
        avg_dt = (dt_in + dt_out) / 2.0
        tangent_mag = data['slope'] * 1.875 / avg_dt

        key.inTangent = -tangent_mag
        key.outTangent = tangent_mag
        key.inTangentLength = orig_data.get('inTangentLength', 0.333)
        key.outTangentLength = orig_data.get('outTangentLength', 0.333)
```

The slope is multiplied by 1.875 and divided by the average gap to the
neighbouring keys, and each key gets back the tangent lengths it had before the
offset. The track ends up with the same keys on the same frames, holding as much of
the shifted motion as those keys can. There is more on that below.

## The whole flow

1. You pick Offset from the Tween button's menu, and the slider turns orange.
2. You press the slider. The selected objects are sorted by hierarchy and given their stagger factors.
3. Each track gets its working range, its original curve is recorded, and it is baked to a key on every frame.
4. You drag. On every update, every key is set from the original curve, offset, wrapped and blended.
5. You let go. Each track is rebuilt down to its original keys, with values and tangents taken from the shifted curve.

## What does not work yet

While writing this post I ran a scripted test of Offset in 3ds Max: test boxes with
Euler, TCB, Linear and XYZ scale tracks, keys with stepped tangents, partly selected
curves and a small hierarchy, with the key counts and values recorded before and
after. Some of what came back I did not expect, and I would rather say it here than
have someone find it in the middle of a shot.

**Peaks can flatten when you let go.** While you drag, the offset is exact. In the
test, a swing from 0 to 90 degrees and back moved six frames earlier and kept its
full shape. But the rebuild only keeps the original key times. If the motion's peak
slides to a frame that has no key, there is no key left to hold it. In that test
the three keys all ended up at 45 degrees, and the tangents could only bring back a
wave between about 25 and 65 degrees instead of the full swing. Curves with only a
few keys, like this one, are hit hardest, because there are fewer keys left to hold
the shape. It is the same problem my December versions were trying to solve, and
keeping the peaks and valleys, like Dense Temporary Keys did, is one of the first
things I want to bring back.

**Some rotation and scale controllers lose their keys.** Offset only understands
tracks whose keys are single numbers, like the separate X, Y and Z tracks of Euler
XYZ rotation and XYZ position or scale. TCB and Linear rotation store a whole
rotation per key, and Max's default Bezier Scale stores three values per key. In
the current version, when you let go of the slider, those tracks lose all their
keys, even if you only clicked without dragging. Going by the code, the same goes
for any other rotation controller that stores a whole rotation per key, such as
Smooth Rotation. Version 1.2 skipped tracks like these, and that check was lost in
the March rewrite. Until it is back, I would only use Offset on objects whose
animated tracks are Euler XYZ rotation and XYZ position or scale. Max's default
Bezier Scale is fine as long as it has no keys.

**Every range is treated as a loop.** Whatever slides off one end comes back in
at the other, which is right for a cycle. On a motion that does not loop, the first
and last keys of the range end up with the same value.

**Selecting only some keys can flatten the curve.** If you select only some keys,
Offset works between them, but the keys outside that range are still read from
inside it and overwritten. In the test I selected two of five keys, dragged to
+10% and let go, and all five keys came back with the same value. The whole curve
went flat.

**Letting go always rebuilds the curve.** Even a click without a drag rebuilds the
keys with custom tangents. In the test that moved the curve by up to about a degree,
and keys with stepped tangents lost their stepping.

**There is no undo block yet.** The offset is not wrapped in an undo, so I would not
rely on Ctrl+Z to take one back.

**Custom attributes and Biped are not offset.** Custom attributes are skipped in
this mode, and selected Biped parts get a normal tween instead.

## What's next

I want to fix these first: putting the check for unsupported tracks back, keeping
the peaks when the curve is rebuilt, only touching keys inside the selected range,
leaving the curve alone when nothing was dragged, and wrapping the whole thing in
an undo. After that, the next post in this series is
the Euler Filter, the "gimbal killer".

## What I learned

Sliding the curve while you drag was the easier part, and every version since
December could do it. Most of the work, and most of the rewrites, went into turning
the result back into keys an animator would want to keep working with. That is also
where most of the bugs I found this time were.

The other lesson is about testing. In December I wrote a test for the one thing I
was worried about, the height of the motion. When I tested it on more kinds of track
and recorded the numbers before and after, it found problems I had never thought to
look for. I should have done that a lot earlier.

---

Animmix is free and available on GitHub. See [the tool page](/tools/animmix/) or go
straight to [the repository](https://github.com/RashedHindash/ANIMMIX).

## References

Hindash, R. (2026, October 1). *Animmix: Building the Tween Machine.* Rashed Hindash. https://rashedhindash.github.io/documentation/animmix-building-the-tween-machine/

Hindash, R. (2026, October 1). *Animmix: Building Time Offset and Stagger.* Rashed Hindash. https://rashedhindash.github.io/documentation/animmix-building-time-offset-and-stagger/
