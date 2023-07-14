---
comment: | 
  WARNING: This file is generated. Any edits will be lost!
title: "Minimal Example Vocabulary"
date: "2023-07-14T10:37:23.960996+00:00"
subtitle: |
  This is an example of a minimal iSamples vocabulary.
execute:
  echo: false
---

Namespace: 
[`https://example.net/my/minimal/vocab`](https://example.net/my/minimal/vocab)

**History**


**Concepts**

  - [thing](#thing)
    - [solid](#solid)
    - [liquid](#liquid)
      - [Water](#water)
      - [Beer](#beer)


## thing
[]{#thing}

Concept: [`thing`](https://example.net/my/minimal/thing

Narrower Concepts:

- https://example.net/my/minimal/solid
- https://example.net/my/extension/liquid

Any physical thing


### solid
[]{#solid}

Concept: [`solid`](https://example.net/my/minimal/solid

Broader Concepts:

- [thing](#thing)

A thing that was considered solid at the time of observation


### liquid
[]{#liquid}

Concept: [`liquid`](https://example.net/my/extension/liquid

Broader Concepts:

- [thing](#thing)

Narrower Concepts:

- [Water](#water)
- [Beer](#beer)

A thing that was considered to be of a liquid state at the time of observation


#### Water
[]{#water}

Concept: [`water`](https://example.net/my/extension/water

Broader Concepts:

- [liquid](#liquid)

A thing that was considered to be liquid water at the time of observation


#### Beer
[]{#beer}

Concept: [`beer`](https://example.net/my/extension2/beer

Broader Concepts:

- [liquid](#liquid)

A thing that was considered to be beer in a liquid state at the time of observation


