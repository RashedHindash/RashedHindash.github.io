# How to run your site

Written for you, not for a developer. You never need to touch code.

---

## The only two things you'll actually use

In this folder there are two files you double-click:

| File | What it does |
| --- | --- |
| **Preview.cmd** | Opens the site on your own computer so you can see changes as you make them. Nobody else can see it. |
| **Publish.cmd** | Puts your changes on the internet. Takes about a minute. |

The normal rhythm is: double-click **Preview**, edit some files, look at the
browser, and when you're happy, close Preview and double-click **Publish**.

---

## Where everything lives

```
RH Studio/
├── Preview.cmd          <- double-click to see your site
├── Publish.cmd          <- double-click to put it online
│
├── content/             <- EVERYTHING YOU EDIT IS IN HERE
│   ├── site.json            your name, tagline, colour, menu, social links
│   ├── work/                one file per project
│   ├── research/            one file per NTRO
│   ├── writing/             one file per blog post
│   ├── tutorials/           one file per tutorial
│   ├── tools/               one file per tool
│   ├── docs/                documentation pages for your tools
│   └── pages/               the About page
│
├── static/              <- images, your CV, anything you link to
│   └── images/
│
├── theme/               <- the design. Ask Claude before changing these.
└── build.py             <- the machinery. Don't open it.
```

**Rule of thumb:** if it's in `content/` or `static/`, it's yours. Everything
else is plumbing.

---

## Writing a blog post

1. Go into `content/writing/`.
2. Copy `welcome.md` and rename the copy — e.g. `blocking-vs-splining.md`.
   The filename becomes the web address, so use dashes, not spaces.
3. Open it in Notepad (or anything).
4. Change the bit at the top between the `---` lines:

```
---
title: Blocking versus splining, ten years later
summary: One sentence that makes someone want to read it.
date: 2026-08-04
tags: [animation, workflow]
---
```

5. Write below the second `---`.

That's it. `# ` makes a big heading, `## ` a smaller one, `**bold**` is bold,
`- ` starts a bullet.

**Not ready to show it yet?** Add `draft: true` under the date. It stays
invisible until you remove that line.

---

## Adding a video (Google Drive)

This is the part with a gotcha, so read it once carefully.

### Step 1 — share the file properly

In Google Drive, right-click your video → **Share** → under *General access*
choose **Anyone with the link**, role **Viewer**.

> If you skip this, the video area will just be blank for visitors — even
> though it plays perfectly for you, because you're signed in. This is the
> single most common problem. If a video looks broken, check this first.

### Step 2 — copy the link

Hit **Copy link**. You'll get something like:

```
https://drive.google.com/file/d/1a2B3c4D5e6F7g8H9i/view?usp=sharing
```

### Step 3 — paste it in

For the **main video at the top of a page**, put it in the top block:

```
---
title: My tutorial
video: https://drive.google.com/file/d/1a2B3c4D5e6F7g8H9i/view
---
```

For a video **in the middle of your writing**, put it on its own line:

```
::video https://drive.google.com/file/d/1a2B3c4D5e6F7g8H9i/view | Optional caption
```

YouTube and Vimeo links work in exactly the same way — just paste the normal
link. So do `.mp4` files you've put in `static/`.

Videos don't load until a visitor clicks play. That's deliberate — it's what
keeps the site fast.

---

## Adding a project to your portfolio

Copy `content/work/example-project.md`, rename it, and edit the top block:

```
---
title: Name of the project
summary: One line describing it.
date: 2026-03-18
role: Lead Animator
client: Who it was for
software: [Maya, Nuke]
featured: true          <- shows it on the front page
cover: /static/images/my-thumbnail.jpg
video: https://drive.google.com/file/d/FILE_ID/view
---
```

`order: 1`, `order: 2` etc. control the sequence on the Work page. Leave it out
and projects sort by date, newest first.

---

## Adding an NTRO

Copy `content/research/example-ntro.md`. It has five extra fields —
**research statement, background, contribution, significance, scope** — which
render as a formal panel at the bottom of the page. That's the format review
panels expect.

Write them like this, with the text indented underneath:

```
research_statement: |
  What question did this work ask?
  It can run over several lines as long as they're indented.
```

Leave any field out and it simply doesn't appear.

---

## Adding a tutorial

Tutorials work exactly like rigs — categories with banners, then items inside.

- `content/tutorial-categories/` — Foundation, Body Mechanics, Animation Tips
- `content/tutorials/` — one file per video

Copy any file in `content/tutorials/` and edit it:

```
---
title: Bouncing Ball (2D)
category: foundation
summary: One line on what the video covers.
video: https://drive.google.com/file/d/FILE_ID/view
thumb: /static/images/tutorials/thumbs/bouncing-ball-2d.jpg
software: 3ds Max
duration: 12 min
order: 1
---
```

Videos **play on the card itself** — nobody leaves the page, and nothing loads
from Google until someone actually presses play.

### Grouping videos into a series

Add a `series:` line and matching videos gather under a heading, numbered by
`order`:

```
category: body-mechanics
series: Turn
order: 3
```

Leave `series` out and the video sits on its own above any series.

### Thumbnails

`thumb:` is optional. Without it the site pulls a still from Google Drive,
which works but is slower and depends on Drive being reachable. Local
thumbnails are better — grab a frame, save it into
`static/images/tutorials/thumbs/`, and point `thumb:` at it.

---

## Adding a rig

Rigs are split into **categories** (Foundational, Body Mechanics, Acting).
Two folders are involved:

- `content/rig-categories/` — one file per category, holds the banner
- `content/rigs/` — one file per rig

### To add a rig to an existing category

1. Put the preview image in `static/images/rigs/<category>/`
2. Put the `.max` file in `static/files/rigs/<category>/`
3. Copy any file in `content/rigs/`, rename it, and edit:

```
---
title: Ball
category: foundational
summary: One line describing what it teaches.
image: /static/images/rigs/foundational/ball.png
download: /static/files/rigs/foundational/Ball.max
software: 3ds Max
order: 1
---
```

`order` sets the position on the page. That's the whole thing — no body text
needed, though you can add some and it'll appear under the title.

**The file size on the download button is worked out automatically.** Replace
the `.max` file with a bigger version and the button updates itself. Don't
type a size anywhere.

### To switch on a new category

`content/rig-categories/body-mechanics.md` and `acting.md` already exist but
have `draft: true` at the top, which hides them. To open one up:

1. Delete the `draft: true` line
2. Add a banner image and point `banner:` at it
3. Add rigs with the matching `category:` value

### Keep the files reasonable

Anything up to about 90 MB per file is fine. If a rig is bigger than that,
tell Claude — it needs hosting a different way, and it's a two-minute change.

::note Downloads come straight from your own site. Visitors never touch Google
Drive, never see a preview screen, and never hit a daily quota limit.

---

## Adding a tool and its documentation

The tool itself goes in `content/tools/` — one file, e.g. `animmix.md`.

Documentation pages go in `content/docs/`, and each one needs a `tool:` line
matching the tool's filename:

```
---
title: Installation
tool: animmix
order: 1
---
```

They appear automatically in a sidebar on every doc page, and as a list on the
tool's own page. Add as many as you like.

---

## Images

1. Put the file in `static/images/`.
2. Refer to it as `/static/images/whatever.jpg`.

In the middle of your writing:

```
::image /static/images/blocking-pass.jpg | Blocking pass, frame 240
```

Several side by side:

```
::grid /static/images/a.jpg | /static/images/b.jpg | /static/images/c.jpg
```

Keep images under about 1600px wide — anything bigger just slows the page down
without looking better.

---

## Your CV

Save it as `static/cv.pdf`. The download link on the About page then works.
Until you do, that one link goes nowhere — so either add the file or delete
that line from `content/pages/about.md`.

---

## Changing your name, tagline, colour or menu

All of it is in `content/site.json`. Keep the quotes and commas exactly where
they are — that file is fussy about punctuation.

The accent colour is one line:

```
"accent": "#ff5c35",
```

Any hex colour works. Change it and the whole site follows, including the
favicon.

---

## When something goes wrong

**Publish.cmd says the site didn't build.**
Something in a file you edited is malformed — usually a missing `---` line, or
a broken quote/comma in `site.json`. The error message names the file. Undo
your last edit and try again.

**A video is blank.**
Sharing permissions. See the Google Drive section above.

**My change isn't on the site.**
Give it two minutes. Then check the **Actions** tab of your GitHub repo — a
green tick means it published, a red cross means it didn't, and clicking it
tells you why.

**I've broken something and I don't know what.**
Nothing is ever lost — every version is stored in GitHub. Ask Claude to roll it
back.

---

## What this site does not do

No comments, no newsletter, no analytics, no cookie banner (nothing is tracked,
so none is needed), no login. If you want any of those later, they can be
added — but each one costs you some of the speed.
