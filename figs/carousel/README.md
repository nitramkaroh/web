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
slide markup to paste into `index.html`. A video slide is muted, loops, and
plays only while its slide is visible; under `prefers-reduced-motion` it does
not autoplay and gets real controls instead.
