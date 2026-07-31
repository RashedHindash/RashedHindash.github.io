---
title: How this site works
summary: A short tour of the site, and a reminder to myself of how to add things to it.
date: 2026-07-31
tags: [meta]
---

<!-- EXAMPLE POST. Delete it once you've written a real one. -->

Every page on this site is a plain text file. There is no database, no login,
no content management system to update, and nothing to pay for. Writing a post
means adding a file to `content/writing/` and pushing it to GitHub. About
forty seconds later the site rebuilds itself.

## The formatting you'll actually use

**Bold**, *italic*, `inline code`, and [links](https://example.com) all work the
way you'd expect. Lists too:

- A bullet
- Another bullet
  - Nested, if you indent by two spaces

1. Or numbered
2. When order matters

> A blockquote, for when someone else said it better.

## Video

Paste a Google Drive share link and it becomes a player:

```
::video https://drive.google.com/file/d/FILE_ID/view | An optional caption
```

YouTube, Vimeo and direct `.mp4` files work the same way. Nothing loads until a
visitor actually clicks play, which is why the pages stay fast.

## Images

```
::image /static/images/my-picture.jpg | An optional caption
```

Drop the file into `static/images/` first and it gets copied across on build.
