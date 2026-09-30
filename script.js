/* Mobile navigation ------------------------------------------------------- */

const navToggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('.site-nav');

if (navToggle && nav) {
  navToggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });

  // Close the menu after following a link on a phone.
  nav.addEventListener('click', (event) => {
    if (event.target.tagName === 'A') {
      nav.classList.remove('is-open');
      navToggle.setAttribute('aria-expanded', 'false');
    }
  });
}

/* Carousel ---------------------------------------------------------------- */

document.querySelectorAll('.carousel').forEach((carousel) => {
  const slides = [...carousel.querySelectorAll('.carousel-slide')];
  if (slides.length === 0) return;

  const dots = carousel.querySelector('.carousel-dots');
  const prev = carousel.querySelector('.carousel-arrow.prev');
  const next = carousel.querySelector('.carousel-arrow.next');
  const single = slides.length === 1;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const interval = Number(carousel.dataset.autoplay) || 0;

  // Inline muted playback is the only kind browsers autoplay. A video loops
  // only when it is the whole carousel; with siblings it plays once and the
  // carousel moves on when it ends. Under reduced motion nothing plays by
  // itself, so those viewers get real controls instead.
  slides.forEach((slide) => {
    const videos = slide.querySelectorAll('video');
    if (videos.length === 0) return;
    slide.classList.add('has-video');
    videos.forEach((video) => {
      video.muted = true;
      video.loop = single;
      video.playsInline = true;
      video.setAttribute('playsinline', '');
      // Fetch the visible animation up front; hidden slides only need metadata.
      video.preload = slide.classList.contains('is-active') ? 'auto' : 'metadata';
      if (reduceMotion) video.controls = true;
    });
  });

  function playIn(slide) {
    let started = false;
    slide.querySelectorAll('video').forEach((video) => {
      video.preload = 'auto';
      if (reduceMotion) return;
      const p = video.play();
      if (p && p.catch) p.catch(() => {});
      started = true;
    });
    slide.classList.toggle('is-playing', started);
    return started;
  }

  function stopIn(slide, rewind) {
    slide.querySelectorAll('video').forEach((video) => {
      video.pause();
      if (rewind) video.currentTime = 0;
    });
    slide.classList.remove('is-playing');
  }

  if (single) {
    carousel.classList.add('is-single');
    slides[0].classList.add('is-active');
    playIn(slides[0]);
    return;
  }

  let index = Math.max(slides.findIndex((s) => s.classList.contains('is-active')), 0);
  let timer = null;
  let token = 0;          // invalidates anything scheduled for a previous slide

  const buttons = slides.map((_, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-label', `Figure ${i + 1} of ${slides.length}`);
    b.addEventListener('click', () => show(i));
    dots?.appendChild(b);
    return b;
  });

  slides.forEach((slide) => {
    slide.querySelectorAll('video').forEach((video) => {
      // If a file cannot play at all, that slide falls back to the timer.
      video.addEventListener('error', () => { slide.dataset.videoBroken = 'true'; });
    });
  });

  function clearTimer() {
    if (timer) { clearTimeout(timer); timer = null; }
  }

  // A video slide hands over when its animation finishes, so nothing is cut
  // off mid-way and nothing sits on a last frame. "ended" is the intended
  // signal, but it does not always fire - a file whose container duration
  // does not match its frames can stall on the final frame instead - so the
  // near-end check and the backstop timer make sure the carousel cannot
  // freeze on a video. Whichever fires first wins; the token discards the rest.
  function scheduleAdvance() {
    clearTimer();
    if (reduceMotion) return;

    const slide = slides[index];
    const video = slide.querySelector('video');
    const mine = token;
    const advance = () => { if (mine === token) show(index + 1); };

    if (video && slide.dataset.videoBroken !== 'true') {
      // duration has to be read live: at the moment a slide is shown the
      // metadata may not have arrived yet and it is still NaN.
      const lengthOf = () =>
        (Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 0);

      const onEnded = () => advance();
      // The backstop is measured from where playback actually is, so a slow
      // buffer extends the deadline instead of cutting the animation short.
      const armBackstop = () => {
        if (mine !== token) return;
        clearTimer();
        const length = lengthOf();
        const remaining = length ? Math.max(length - video.currentTime, 0) * 1000
                                 : (interval || 7000);
        timer = setTimeout(advance, remaining + 600);
      };

      // timeupdate fires roughly every 250 ms, so the window has to be wider
      // than that or the last event lands outside it and the backstop wins.
      const onTime = () => {
        const length = lengthOf();
        if (length && video.currentTime >= length - 0.35) { advance(); return; }
        armBackstop();
      };

      video.addEventListener('ended', onEnded, { once: true });
      video.addEventListener('timeupdate', onTime);
      video.addEventListener('loadedmetadata', armBackstop, { once: true });
      // Detach when this slide is left, so listeners do not pile up.
      slide._carouselCleanup = () => {
        video.removeEventListener('ended', onEnded);
        video.removeEventListener('timeupdate', onTime);
        video.removeEventListener('loadedmetadata', armBackstop);
      };

      armBackstop();
    } else if (interval > 0) {
      timer = setTimeout(advance, interval);
    }
  }

  function show(i) {
    token += 1;
    slides.forEach((slide) => {
      if (slide._carouselCleanup) { slide._carouselCleanup(); slide._carouselCleanup = null; }
    });
    index = (i + slides.length) % slides.length;
    slides.forEach((slide, k) => {
      const on = k === index;
      slide.classList.toggle('is-active', on);
      slide.setAttribute('aria-hidden', String(!on));
      slide.querySelectorAll('a').forEach((a) => {
        if (on) { a.removeAttribute('tabindex'); } else { a.setAttribute('tabindex', '-1'); }
      });
      if (on) { playIn(slide); } else { stopIn(slide, true); }
    });
    buttons.forEach((b, k) => b.setAttribute('aria-selected', String(k === index)));
    scheduleAdvance();
  }

  prev?.addEventListener('click', () => show(index - 1));
  next?.addEventListener('click', () => show(index + 1));

  carousel.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') show(index - 1);
    if (event.key === 'ArrowRight') show(index + 1);
  });

  // Swipe on touch devices.
  let startX = null;
  carousel.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; }, { passive: true });
  carousel.addEventListener('touchend', (e) => {
    if (startX === null) return;
    const dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 40) show(dx < 0 ? index + 1 : index - 1);
    startX = null;
  }, { passive: true });

  show(index);
});
