# Hero carousel images

Drop image files in this folder and list them in the `.carousel` block in
`index.html`. One `<li class="carousel-slide">` per image:

```html
<li class="carousel-slide">
  <figure>
    <img src="figs/carousel/02-my-figure.jpg" alt="What the figure shows" loading="lazy" />
    <figcaption>Short caption &mdash; <em>Journal</em>, 2026</figcaption>
  </figure>
</li>
```

The carousel hides its controls when there is only one slide, so it is safe
to start with one and add more later.

Sizing: the hero figure column is at most 420 px wide on a desktop, so an
image about **840 px wide** covers a 2x display. Anything smaller is shown
at its native size rather than upscaled, to keep it sharp. Landscape crops
around 3:2 fit the frame with least letterboxing.


## Animations

ParaView writes Motion-JPEG AVI, which no browser plays. Convert first:

```bash
tools/make-carousel-video.sh path/to/HorseShoe.avi 02-horseshoe
```

That writes `02-horseshoe.mp4` (H.264) plus a poster frame, and prints the
slide markup to paste into `index.html`.

A video slide is muted and plays only while its slide is visible. What happens
when it finishes depends on how many slides there are:

- **one slide** &mdash; it loops, since there is nowhere to go
- **more than one** &mdash; it plays once and the carousel moves to the next
  slide as soon as the animation ends, so nothing is cut off mid-way and
  nothing sits on a last frame

Image slides advance on the `data-autoplay` interval instead. Under
`prefers-reduced-motion` nothing autoplays or auto-advances, and videos get
real controls.
