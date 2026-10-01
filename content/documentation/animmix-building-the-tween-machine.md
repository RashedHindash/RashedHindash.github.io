---
title: Animmix: Building the Tween Machine
summary: How the first tool in Animmix works under the hood, from the maths behind a single slider to the parts of 3ds Max that made it harder than it looked.
date: 2026-10-01
tags: [animmix, tools, 3ds max, python, development]
---

In [my first post about Animmix](/documentation/animmix-how-its-made/), I explained
that the whole toolkit started with a Tween Machine. It was the first tool I
built, and almost everything that came after it grew out of the same slider. This
post goes through how it actually works: the maths, the way it reads the scene,
the parts of 3ds Max that made it harder than it should have been, and the slider
itself.

It is a technical post, and there is a lot of code in it. Everything here comes
from the current version of Animmix for 3ds Max 2026 and later, written in Python
with pymxs and PySide6.

## What a Tween Machine is

If you have animated in Maya, you have probably used tweenMachine, Justin Barrett's
script, at some point. The idea is simple. You are sitting on a frame between two
keys, and you want to push the pose towards one side or the other without opening
the Graph Editor. You drag a slider and the frame is keyed as you go. No tangents to
adjust, no curves to touch, just one slider.

I knew it had to be the first thing I built for Max. It is the tool animators
reach for hundreds of times a day. If I could get that one interaction to feel
fast and reliable, everything else would have something solid to sit on.

The goal was a slider that reads the previous and next keys on everything
selected, blends between them while you drag, and writes the result back to the
scene every time the slider moves. It had to handle position, rotation, scale and
custom attributes, all in one pass.

## The maths

Everything the Tween Machine does comes down to one operation, linear
interpolation, usually shortened to lerp:

```python
# The tween formula
result = prev_value + (next_value - prev_value) * t

# prev_value is the value at the key before the current frame
# next_value is the value at the key after it
# t = 0.0 is all previous, t = 1.0 is all next, t = 0.5 is halfway
```

The slider runs from -100 to +100, so its value has to be turned into a t between
0 and 1. That happens in two steps. The slider callback divides by 100 to get a
value from -1 to +1, and in Tween mode the tween function then shifts that into
the 0 to 1 range:

```python
# In the slider callback: -100..100 becomes -1..1
t = val / 100.0

# In apply_cached_tween(): -1..1 becomes 0..1
t = (tween_amount + 1.0) / 2.0

# -100 gives 0.0, all previous key
#    0 gives 0.5, an even blend
# +100 gives 1.0, all next key
```

That is the whole mathematical core. Everything else is infrastructure: finding
the right keys, reading their values, writing the result back, and doing all of
that quickly enough that it feels instant.

## Reading the scene once

When the slider is pressed, values need to start changing straight away. Querying
the scene on every tick of the slider would be too slow. It would also lose
information, because the moment the slider writes its first key, the pose that was
on that frame before is gone. So the tool reads everything it needs once, when the
slider is pressed, keeps it in a cache, and from then on only does maths on that
cache.

Each animated controller gets one entry in that cache, a `TweenData` object:

```python
class TweenData:
    __slots__ = ['obj', 'prop', 'ctrl', 'sub_ctrls', 'is_euler', 'is_xyz',
                 'prev_key', 'next_key', 'prev_val', 'next_val', 'orig_val']
```

It holds the scene node, which property it is (position, rotation or scale), the
controller, its X, Y and Z sub-controllers if it has them, two flags describing
what kind of controller it is, the frames of the keys on either side, and three
sets of values.

`__slots__` is a small Python optimisation. Normally every object keeps its
attributes in a dictionary, which has overhead. With `__slots__`, Python uses a
fixed layout instead, which uses less memory. On a large rig the tool can create
hundreds of these at once, so it is worth having.

There are three sets of values because the modes do not all blend the same way.
`prev_val` and `next_val` are the keys on either side, and they never change
during a drag. `orig_val` is whatever the curve was doing on the current frame
before the slider was touched. Default mode works from that original value rather
than between the two keys. Tween, Space and Default all share this structure. The
other modes need different data, so they build caches of their own.

## Building the cache

`build_cache()` runs when the slider is pressed. It goes through every selected
object and every transform property, finds the keys on either side of the current
frame, reads the values at those keys, and stores everything in one dictionary:

```python
_cache = {'valid': False, 'ct': 0, 'items': [], 'ca_items': [], 'obj_items': {}}
```

`valid` says whether anything worth tweening was found, and `ct` is the frame the
cache was built on. `items` holds the `TweenData` entries for transforms, and
`ca_items` holds custom attributes. `obj_items` is the same transform data grouped
by object, so the position, rotation and scale of one object can be looked up
together.

Keeping transforms and custom attributes apart is deliberate. Transforms live on
the node's controller tracks. Custom attributes, things like IK/FK blends or finger
curls, live on Attribute Holder modifiers, and they have to be read and written in
a completely different way.

### Finding the keys on either side

For each controller, the tool collects every key time, including the keys on any
separate X, Y and Z tracks, and then looks for the nearest key on each side of the
current frame:

```python
ct_int = int(rt.currentTime)
key_times = get_all_key_times(ctrl)    # sorted, no duplicates
if len(key_times) < 2: continue

prev_key = next((t for t in reversed(key_times) if t < ct_int), None)
next_key = next((t for t in key_times if t > ct_int), None)

# It needs a key on both sides, otherwise there is nothing to blend between
if prev_key is None or next_key is None: continue
```

Searching the list backwards means the first match is automatically the closest
key before the current frame, and `next()` stops as soon as it finds it. No extra
sorting or bookkeeping is needed.

### Reading values on other frames

To read a value on a different frame without moving the time slider, pymxs has
`attime()`. Inside it, Max evaluates the controller as if it were on that frame:

```python
data.prev_val = [0.0]*3; data.next_val = [0.0]*3; data.orig_val = [0.0]*3

for time_val, target_list in [(prev_key, data.prev_val),
                              (next_key, data.next_val),
                              (ct_int, data.orig_val)]:
    with pymxs.attime(time_val):
        for i, sc in enumerate(sub_ctrls):
            if sc: target_list[i] = float(sc.value)
```

That is the path for controllers with separate X, Y and Z tracks. Controllers that
store a single value, such as a quaternion rotation, are read the same way, but the
whole value is copied with `rt.copy(ctrl.value)`.

`attime()` does not move the time slider, so the viewport does not flicker while
the cache is being built.

## The hard part: resolving controllers

This is the part that catches almost everyone the first time they work with 3ds Max
controllers in Python. The controller you get from a track is not always the one
holding the keys. In Max, controllers are very often wrapped in list controllers.
Freezing the transforms on a control does exactly that, and most rigs freeze
their controls. Those layers have to be drilled through.

### List controllers

A list controller (Position List, Rotation List, Scale List or Float List) is a
stack of layers, a little like a layer stack in Photoshop. Every layer is evaluated
and combined by weight, and one of them is the active layer, the one that receives
your changes in the viewport. When you freeze transforms, Max makes a list with a
frozen layer holding the rest pose and an animation layer on top, and sets the
animation layer as active.

If you ask Max for a control's rotation controller and get a Rotation List back,
the keys are not on the list itself. They are on the active layer inside it. The tool spots a
list controller by checking for the `weight` and `count` properties that list
controllers have, and `resolve_controller()` digs down to the active layer:

```python
def is_list_controller(ctrl):
    if not ctrl: return False
    try:
        return rt.isProperty(ctrl, "weight") and rt.isProperty(ctrl, "count")
    except: return False

def resolve_controller(ctrl):
    if ctrl is None: return None

    loop_guard = 0
    # Lists can be nested, so keep going down
    while is_list_controller(ctrl) and loop_guard < 5:
        loop_guard += 1
        try:
            active_idx = ctrl.getActive()    # 1-based in Max
            if active_idx is None or active_idx < 1:
                break

            sub_found = None
            try:
                # 0-based access first
                item = ctrl[active_idx - 1]
                if hasattr(item, 'controller') and item.controller:
                    sub_found = item.controller
                else:
                    sub_found = item
            except:
                try:
                    # Fall back to 1-based access
                    item = ctrl[active_idx]
                    if hasattr(item, 'controller') and item.controller:
                        sub_found = item.controller
                    else:
                        sub_found = item
                except: pass

            if sub_found:
                ctrl = sub_found    # one level deeper
            else:
                break
        except: break

    return ctrl
```

The loop guard stops the function running forever if a rig has a broken controller
chain. The two ways of indexing are there because MaxScript counts from 1 and Python
counts from 0. `getActive()` returns a MaxScript index, so the code first tries it
minus one, the way Python would count, and if that fails it tries the index as Max
gives it. It is a safety net, so the tool keeps working whichever way the wrapper
expects it.

### Separate X, Y and Z tracks

Once the top controller is resolved, the tool needs to know whether it stores one
value for all three axes or three separate float tracks. Position XYZ, Euler XYZ
and Scale XYZ use separate tracks, and each axis has to be set on its own:

```python
def is_xyz_controller(ctrl):
    if ctrl is None: return False
    name = str(rt.classof(ctrl)).lower()
    return "xyz" in name or "euler" in name

def is_euler_rotation(ctrl):
    if ctrl is None: return False
    cls = rt.classof(ctrl)
    return cls == rt.Euler_XYZ or "euler" in str(cls).lower()
```

For those controllers it collects the three sub-tracks, and resolves each one
again:

```python
sub_ctrls = []
for i in range(3):    # 0 = X, 1 = Y, 2 = Z
    try:
        sub = ctrl[i]
        sub_ctrl = sub.controller if hasattr(sub, 'controller') else sub
        sub_ctrl = resolve_controller(sub_ctrl)    # the track may be a list too
        sub_ctrls.append(sub_ctrl)
    except: sub_ctrls.append(None)
```

Resolving the sub-tracks matters. In some rigs the individual X, Y and Z tracks are
themselves wrapped in Float List controllers. The keys live on the layer inside
each list, so without resolving them, the tool would not find the keys it needs to
blend between.

## Applying the tween

`apply_cached_tween()` runs every time the slider moves, so it has to be quick. It
turns the slider amount into t, loops over the cache, and writes the blended values
back to the scene.

The real function has branches for several modes. Tween and Space blend between
the two keys, and Default blends the current pose towards the rest pose: zero
position and rotation, and a scale of one. To keep it readable, this is the part
that does the plain tween:

```python
def apply_cached_tween(tween_amount, mode):
    global _cache
    if not _cache['valid']: return False
    ct = rt.currentTime
    t = (tween_amount + 1.0) / 2.0

    with pymxs.attime(ct):
        with pymxs.animate(True):
            for items in _cache['obj_items'].values():

                # Position
                if items['position']:
                    d = items['position']
                    res = lerp3(d.prev_val, d.next_val, t)
                    if d.is_xyz and d.sub_ctrls:
                        for i, sc in enumerate(d.sub_ctrls):
                            if sc: sc.value = res[i]
                    else:
                        d.ctrl.value = rt.Point3(res[0], res[1], res[2])

                # Rotation
                if items['rotation']:
                    d = items['rotation']
                    if d.is_euler and d.is_xyz and d.sub_ctrls:
                        res = lerp3(d.prev_val, d.next_val, t)
                        for i, sc in enumerate(d.sub_ctrls):
                            if sc: sc.value = res[i]
                    else:
                        # Quaternion rotation uses slerp, not lerp
                        d.ctrl.value = rt.slerp(d.prev_val, d.next_val, t)

                # Scale
                if items['scale']:
                    d = items['scale']
                    res = lerp3(d.prev_val, d.next_val, t)
                    if d.is_xyz and d.sub_ctrls:
                        for i, sc in enumerate(d.sub_ctrls):
                            if sc: rt.addNewKey(sc, ct).value = res[i]
                    else:
                        if d.ctrl: rt.addNewKey(d.ctrl, ct)
                        d.ctrl.value = rt.Point3(res[0], res[1], res[2])

            # Custom attributes are handled here too (see below)

    rt.completeRedraw()
    return True
```

### lerp and lerp3

```python
def lerp(a, b, t): return a + (b - a) * t
def lerp3(a, b, t): return [a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t, a[2]+(b[2]-a[2])*t]
```

These are deliberately plain: no numpy, no dependencies, just Python arithmetic.
For three numbers that is actually quicker than numpy, because there is no
conversion overhead.

### Why rotation is handled two ways

This is one of the most important things to understand when building animation
tools for Max. A rotation can be stored in two quite different ways. Euler XYZ keeps
three separate angles. Max's other rotation controllers, such as TCB, Linear and
Smooth Rotation, keep a single quaternion, and the tool treats anything that is not
Euler that way:

| Euler XYZ | Quaternion |
|---|---|
| Three separate float tracks | A single quaternion value |
| Each axis can be animated on its own | All three axes change together |
| Can suffer from gimbal lock | No gimbal lock |
| Blended per axis with `lerp3()` | Blended with `rt.slerp()` |
| Set through each sub-controller | Set on the controller as one value |

Blending the four numbers of a quaternion directly does not give a proper rotation.
Even when the result is normalised, the rotation does not move at an even speed
between the two poses. `slerp` blends along the arc between them at a constant
rate, so quaternion rotations always go through `rt.slerp()`.

## animate() and attime()

These two context managers do a lot of the work of making this behave properly
inside Max, so they are worth understanding.

### pymxs.animate(True)

In 3ds Max, changing a controller's value from a script does not create a key
unless animation is switched on, the same way nothing is keyed by hand without Auto
Key. To make sure keys are actually written, the change has to happen inside an
animate context:

```python
# Without animate: changes the value, but no key is created
ctrl.value = 45.0

# With animate: creates a key on the current frame
with pymxs.animate(True):
    ctrl.value = 45.0
```

### pymxs.attime()

As above, this sets the frame that reads and writes happen on, without moving the
time slider. The Tween Machine uses it in two places: reading the values at the keys
on either side when the cache is built, and writing the result on the current
frame:

```python
# Reading a value on frame 10 without scrubbing
with pymxs.attime(10):
    val = float(ctrl.value)

# Writing a value on the current frame
with pymxs.attime(rt.currentTime):
    with pymxs.animate(True):
        ctrl.value = new_value
```

`animate(True)` on its own keys whichever frame Max is evaluating at that moment.
Wrapping the write in `attime()` as well makes the frame explicit. The frame is
captured once at the start of each pass, and every write in that pass lands on it.

## Custom attributes

A character rig is not just bones and IK. Almost every production rig has custom
float attributes for things like IK/FK switching, finger curls or eye targets. They
are stored as custom attributes, often on Attribute Holder modifiers, rather than on
the transform controllers, so they need their own path through the cache and the
apply step.

### Finding them

```python
def get_all_custom_attribute_defs(obj):
    ca_defs = []
    try:
        # On the object itself
        num_ca = rt.custAttributes.count(obj)
        for i in range(1, num_ca + 1):
            ca_def = rt.custAttributes.get(obj, i)
            if ca_def: ca_defs.append((obj, i, ca_def))
        # And on each of its modifiers
        if rt.isProperty(obj, rt.Name("modifiers")):
            for m in obj.modifiers:
                try:
                    num_ca = rt.custAttributes.count(m)
                    for i in range(1, num_ca + 1):
                        ca_def = rt.custAttributes.get(m, i)
                        if ca_def: ca_defs.append((m, i, ca_def))
                except: pass
    except: pass
    return ca_defs
```

It looks in two places: the object itself, and every modifier on its stack.
Attribute Holders are the usual home, but custom attributes can sit on other
modifiers or straight on the object, so it checks all of them.

### Tweening them

They use exactly the same formula as the transforms:

```python
for ca_data in _cache['ca_items']:
    prev, nxt = ca_data['prev_val'], ca_data['next_val']
    result = lerp(prev, nxt, t)

    try:
        ca = rt.custAttributes.get(ca_data['owner'], ca_data['ca_index'])
        rt.setProperty(ca, ca_data['param_name'], result)
    except: pass
```

## Biped

Biped does not keep its animation in ordinary controllers, so none of the above
works on it directly. It gets its own cache, built at the same moment as the main
one, and it follows the same idea: find the keys on either side of the current
frame, store the position and rotation at each, and blend between them while the
slider moves. Anything in Figure Mode is skipped.

## The slider

A standard Qt slider is a grey bar with a pill-shaped handle. That is fine in a
settings window, but it felt wrong for an animation tool. I wanted something that
reads clearly at a glance: a dark track, a coloured fill that shows which way you
are dragging and how far, a percentage readout, and markers for the values you snap
to most often.

`AnimmixSlider` is a subclass of `QSlider` that draws itself from scratch:

```python
class AnimmixSlider(QtWidgets.QSlider):
    def __init__(self, parent=None):
        super().__init__(QtCore.Qt.Horizontal, parent)
        self.setRange(-100, 100)
        self.setValue(0)
        self.active_color = QtGui.QColor("#32CD32")    # green until a mode sets it
        self.is_active = False                         # True while it is held

    def set_color(self, color_str):
        self.active_color = QtGui.QColor(color_str)
        self.update()
```

### Drawing it

`paintEvent()` draws the slider in layers: the dark track, the coloured fill from
the centre to the handle, the marker dots, the handle, and finally the percentage,
which only appears when the slider is away from the centre. It is drawn on the side
away from the handle, so the two never overlap. While the slider is held, the track
thickens from 6 to 16 pixels and the handle grows, so it is obvious you are in the
middle of a drag.

```python
def paintEvent(self, event):
    painter = QtGui.QPainter(self)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    rect = self.rect()
    center_y = rect.height() / 2
    margin = 16
    usable_width = rect.width() - (margin * 2)
    track_height = 16 if self.is_active else 6
    track_radius = track_height / 2
    val = self.value()
    range_len = self.maximum() - self.minimum()
    norm = (val - self.minimum()) / range_len
    handle_x = margin + (norm * usable_width)
    center_x = rect.width() / 2

    # Track
    painter.setPen(QtCore.Qt.NoPen)
    painter.setBrush(QtGui.QColor("#1A1A1A"))
    painter.drawRoundedRect(margin, int(center_y - track_radius), int(usable_width),
                            int(track_height), track_radius, track_radius)

    # Fill, from the centre to the handle
    painter.setBrush(self.active_color)
    if val != 0:
        if val > 0:
            w = handle_x - center_x
            r = QtCore.QRectF(center_x, center_y - track_radius, w, track_height)
        else:
            w = center_x - handle_x
            r = QtCore.QRectF(handle_x, center_y - track_radius, w, track_height)
        painter.drawRoundedRect(r, track_radius, track_radius)

    # Marker dots
    painter.setBrush(QtGui.QColor("#444"))
    for tick_val in [-100, -75, -50, -25, 0, 25, 50, 75, 100]:
        tick_norm = (tick_val - self.minimum()) / range_len
        tick_x = margin + (tick_norm * usable_width)
        radius = 1.0 if abs(tick_val) in [25, 50, 75] else 1.5
        painter.drawEllipse(QtCore.QPointF(tick_x, center_y), radius, radius)

    # Handle
    handle_radius = 8 if self.is_active else 6
    painter.setBrush(self.active_color)
    painter.setPen(QtGui.QPen(QtGui.QColor("#111"), 2))
    painter.drawEllipse(QtCore.QPointF(handle_x, center_y), handle_radius, handle_radius)

    # Percentage, only away from the centre
    if val != 0:
        text_str = f"{val}%"
        painter.setFont(QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold))
        painter.setPen(QtGui.QColor("white"))
        txt_pad = 10
        left_bound = margin + txt_pad
        right_bound = rect.width() - margin - txt_pad
        if val > 0:
            t_rect = QtCore.QRectF(left_bound, 0, 100, rect.height())
            painter.drawText(t_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter, text_str)
        else:
            t_rect = QtCore.QRectF(right_bound - 100, 0, 100, rect.height())
            painter.drawText(t_rect, QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter, text_str)

    painter.end()
```

The `is_active` flag is switched on when the mouse goes down on the slider and off
when it comes back up, which is what makes it redraw in the thicker style.

### Connecting it to the scene

Three signals drive the whole thing. Pressing the slider builds the caches, every
movement applies the result, and letting go clears everything and puts the slider
back in the centre:

```python
self.slider.sliderPressed.connect(self.sl_press)
self.slider.sliderReleased.connect(self.sl_release)
self.slider.valueChanged.connect(self.sl_change)

def sl_press(self):
    # Back to the centre without triggering sl_change
    self.slider.blockSignals(True)
    self.slider.setValue(0)
    self.slider.blockSignals(False)

    build_biped_cache()
    if self.mode == 3:
        build_offset_cache()
    elif self.mode == 6:
        build_pushpull_cache()
    elif self.mode == 7:
        build_simplify_cache()
    elif self.mode == 8:
        build_favor_cache()
    elif self.mode == 9:
        build_smooth_cache()
    elif self.mode == 10:
        build_noise_cache()
    elif self.mode != 4:
        build_cache()

def sl_change(self, val):
    t = val / 100.0
    apply_biped_tween(t, self.mode)
    finalize_selected_keys(t, self.mode)

def sl_release(self):
    clear_cache()
    clear_pushpull_cache()
    clear_offset_cache()
    clear_favor_cache()
    clear_simplify_cache()
    clear_smooth_cache()
    clear_noise_cache()
    self.slider.blockSignals(True)
    self.slider.setValue(0)
    self.slider.blockSignals(False)
```

Most modes build their own cache when the slider is pressed, because each one needs
different data. Blend builds nothing up front.

Putting the slider back to zero would normally fire `valueChanged` and run the
tween again at zero, which in Tween mode is the even 50/50 blend. Every release
would throw away the pose you just made and replace it with the halfway pose.
Blocking the slider's signals around `setValue(0)` lets it reset visually without
anything being applied.

## Snap points

Above the slider there is a row of small dots. Each one is a one-click snap:
clicking it is the same as pressing the slider, dragging it to that value and
letting go. It builds the cache, applies the value, and clears up again. In Tween
mode, the centre dot gives the exact inbetween, -100 goes all the way to the
previous key, and 50 sits three-quarters of the way towards the next key.

```python
def snap_click(self, val):
    self.sl_press()              # build the caches
    self.slider.setValue(val)    # triggers sl_change, which applies the tween
    self.sl_release()            # clear the caches and reset the slider
```

The dots are created when the interface is built. They are deliberately different
sizes: 0 and the two ends are larger, and the values in between are smaller, so the
ones you use most stand out:

```python
snap_values = [-100, -75, -50, -25, 0, 25, 50, 75, 100]
for i, val in enumerate(snap_values):
    is_tiny = abs(val) in [25, 50, 75]
    size = 4 if is_tiny else 6
    b = QtWidgets.QPushButton()
    b.setFixedSize(size, size)    # drawn round through the style sheet
    b.setProperty("base_size", size)
    b.clicked.connect(lambda c=False, v=val: self.snap_click(v))
    self.anchor_layout.addWidget(b)
    self.snap_btns.append(b)
    if i < len(snap_values) - 1:
        self.anchor_layout.addStretch(1)    # even spacing between the dots
```

The `v=val` in the lambda is important. It copies the value of `val` into the
lambda at the moment the button is made. Without it, every button would point at
the same variable, and they would all snap to 100, the last value in the loop. It
is a very common Python mistake with lambdas created inside a loop.

## Modes and colours

The slider is not only a tween. Switching mode runs a different operation through
the same slider: Tween, Space, Offset, Blend, Simplify, Favor, Default, Smooth and
Noise. There is a tenth, Push/Pull, which is already in the code with its own
colour, but it does not have a button yet. Each mode has its own colour, so you can
tell which one is active from the slider alone, without reading the buttons:

```python
def set_mode(self, m):
    self.mode = m
    clear_cache()
    clear_pushpull_cache()

    cols = {
        1: "#32CD32",   # Tween, green
        2: "#00CED1",   # Space, teal
        3: "#FFA500",   # Offset, orange
        4: "#FFD700",   # Blend, gold
        5: "#AAAAAA",   # Default, grey
        6: "#FF4444",   # Push/Pull, red (no button yet)
        7: "#8A2BE2",   # Simplify, purple
        8: "#FF69B4",   # Favor, pink
        9: "#87CEEB",   # Smooth, sky blue
        10: "#FF6347",  # Noise, tomato
    }
    c = cols.get(m, "#32CD32")
    self.slider.set_color(c)

    # Light up the button the mode belongs to
    act = f"background-color: {c}; color: #111; border: 1px solid {c}; font-weight: bold;"
    self.btn_tween.setStyleSheet(act if m in [1, 2, 3] else "")
    self.btn_ease.setStyleSheet(act if m in [4, 7] else "")
    self.btn_favor.setStyleSheet(act if m in [8, 5, 9, 10] else "")
```

The real function also updates the button labels and recolours the snap dots to
match the mode.

## The router

Every movement of the slider ends up in `finalize_selected_keys()`, which decides
what actually runs. Modes with their own cache go to their own function. The rest
share the `TweenData` cache and go through `apply_cached_tween()`:

```python
def finalize_selected_keys(tween_amount, mode):
    if mode == 3:  return apply_time_offset(tween_amount)   # Offset
    if mode == 4:  return do_ease(tween_amount)             # Blend
    if mode == 6:  return apply_pushpull(tween_amount)      # Push/Pull
    if mode == 7:  return apply_simplify(tween_amount)      # Simplify
    if mode == 8:  return apply_favor(tween_amount)         # Favor
    if mode == 9:  return apply_smooth(tween_amount)        # Smooth
    if mode == 10: return apply_noise(tween_amount)         # Noise

    # Tween, Space and Default use the shared cache
    if _cache['valid']:
        return apply_cached_tween(tween_amount, mode)

    # If the cache was never built, build it, apply once, and clear it
    build_cache()
    if _cache['valid']:
        result = apply_cached_tween(tween_amount, mode)
        clear_cache()
        return result
    return False
```

## Overshoot

By default the slider runs from -100 to +100, so it can only reach values between
the two keys. Overshoot widens it to -200 to +200, which lets you push past the
keys. It is useful for exaggerating arcs and secondary motion.

```python
def toggle_overshoot(self):
    self.overshoot = not self.overshoot
    self.btn_overshoot.setText(f"Overshoot: {'ON' if self.overshoot else 'OFF'}")
    self.slider.setRange(-200 if self.overshoot else -100,
                         200 if self.overshoot else 100)
```

No extra maths is needed. The lerp formula already handles a t outside 0 to 1:
below 0 it carries on past the previous key, and above 1 it carries on past the
next one. Overshoot is just a wider slider.

## Cleaning up

When the slider is released, the cache is no longer needed. Clearing it does two
things: it lets go of the references to scene objects, which avoids trouble if
those objects are deleted, and it makes sure the next drag starts with fresh data.

```python
def clear_cache():
    global _cache
    # Explicitly break the pymxs references
    for item in _cache.get('items', []):
        item.obj = None
        item.ctrl = None
        item.sub_ctrls = None
    _cache = {'valid': False, 'ct': 0, 'items': [], 'ca_items': [], 'obj_items': {}}
```

The pymxs wrappers around scene nodes and controllers hold on to the objects on
the 3ds Max side. The function breaks those references explicitly before resetting
the cache, so nothing keeps hold of scene nodes once the drag is over.

## The whole flow

From pressing the slider to letting go:

1. You press the slider.
2. It resets to the centre without applying anything, then builds the Biped cache and the cache for the current mode. For a plain tween, `build_cache()` goes through every selected object and property, finds the keys on either side, reads their values with `attime()` and stores everything.
3. You drag it to, say, +67.
4. `sl_change()` turns that into 0.67 and passes it on. `apply_cached_tween()` converts it to a t of 0.835 and writes `lerp(prev, next, 0.835)` on every cached track, inside `animate(True)` and `attime()`.
5. `completeRedraw()` updates the viewport.
6. Steps 4 and 5 repeat every time the slider moves.
7. You let go. Every cache is cleared, and the slider goes back to the centre with its signals blocked.
8. The last value written is now a real key in the scene.

## Mistakes that are easy to make

| Problem | Fix |
|---|---|
| A value is set but no key is written | Set it inside `pymxs.animate(True)` |
| Resetting the slider applies the tween again | Block the slider's signals around `setValue(0)` |
| Buttons made in a loop all snap to the last value | Capture it as a default argument: `lambda c=False, v=val: ...` |
| No keys are found on a frozen control | Run `resolve_controller()` first, on the controller and on each sub-track |
| A quaternion rotation blends unevenly | Use `rt.slerp()`, not a per-number lerp |
| The cache goes stale between drags | Clear it when the slider is released |

## What's next

That is the whole Tween Machine: the maths, the controller resolution, the slider,
and the way it is all wired together. Every part is there for a reason, and
together they make something that feels quick and dependable to use.

In the next post I will cover the Time Offset and Stagger tool. Instead of blending
values, it slides animation in time, and it can stagger a hierarchy so that children
trail behind their parents, or lead ahead of them. That means baking curves down to
a key on every frame, sampling those baked curves, and shifting them in time while
you drag.

The posts I have planned for this series:

1. The Tween Machine (this post)
2. Time Offset and Stagger
3. The Euler Filter, or gimbal killer
4. Mirroring and flipping poses
5. The motion trail
6. Selection sets
7. Animation recovery

## What I learned

The maths behind the Tween Machine fits on one line. Nearly all of the work went
into everything around it: reading the scene once instead of on every tick, getting
through list controllers, treating Euler and quaternion rotations differently, and
making sure keys land exactly where they should. That is the difference between a
slider that technically works and one an animator will trust and reach for without
thinking.

---

Animmix is free and available on GitHub. See [the tool page](/tools/animmix/) or go
straight to [the repository](https://github.com/RashedHindash/ANIMMIX).

## References

::cite Hindash, R. (2026, March 3). *Animmix: How It's Made?* Rashed Hindash. https://rashedhindash.github.io/documentation/animmix-how-its-made/

::cite Hindash, R. (2026, October 1). *Animmix: Building the Tween Machine.* Rashed Hindash. https://rashedhindash.github.io/documentation/animmix-building-the-tween-machine/
