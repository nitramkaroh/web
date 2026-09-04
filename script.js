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

  // One figure is not a carousel: keep it visible, drop the controls.
  const reduceMotionOnly = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (slides.length === 1) {
    carousel.classList.add('is-single');
    slides[0].classList.add('is-active');
    slides[0].querySelectorAll('video').forEach((video) => {
      slides[0].classList.add('has-video');
      video.muted = true;
      video.loop = true;
      video.playsInline = true;
      video.setAttribute('playsinline', '');
      if (reduceMotionOnly) { video.controls = true; return; }
      const started = video.play();
      if (started && started.catch) started.catch(() => {});
      slides[0].classList.add('is-playing');
    });
    return;
  }

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Inline muted playback is the only kind browsers autoplay. Under reduced
  // motion nothing plays by itself, so give those viewers real controls.
  slides.forEach((slide) => {
    const videos = slide.querySelectorAll('video');
    if (videos.length === 0) return;
    slide.classList.add('has-video');
    videos.forEach((video) => {
      video.muted = true;
      video.loop = true;
      video.playsInline = true;
      video.setAttribute('playsinline', '');
      video.preload = 'metadata';
      if (reduceMotion) video.controls = true;
    });
  });
  const interval = Number(carousel.dataset.autoplay) || 0;
  let index = Math.max(slides.findIndex((s) => s.classList.contains('is-active')), 0);
  let timer = null;

  const buttons = slides.map((_, i) => {
    const b = document.createElement('button');
    b.type = 'button';
    b.setAttribute('role', 'tab');
    b.setAttribute('aria-label', `Figure ${i + 1} of ${slides.length}`);
    b.addEventListener('click', () => { show(i); restart(); });
    dots?.appendChild(b);
    return b;
  });

  function show(i) {
    index = (i + slides.length) % slides.length;
    slides.forEach((slide, k) => {
      const on = k === index;
      slide.classList.toggle('is-active', on);
      slide.setAttribute('aria-hidden', String(!on));
      // Keep hidden slides out of the tab order.
      slide.querySelectorAll('a').forEach((a) => {
        if (on) { a.removeAttribute('tabindex'); } else { a.setAttribute('tabindex', '-1'); }
      });
      // Only the visible slide is allowed to play; the rest rewind and stop,
      // so nothing decodes video off-screen.
      slide.querySelectorAll('video').forEach((video) => {
        if (on && !reduceMotion) {
          const started = video.play();
          if (started && started.catch) started.catch(() => {});   // autoplay refused
          slide.classList.add('is-playing');
        } else {
          video.pause();
          if (!on) video.currentTime = 0;
          slide.classList.remove('is-playing');
        }
      });
    });
    buttons.forEach((b, k) => b.setAttribute('aria-selected', String(k === index)));
  }

  function restart() {
    if (timer) clearInterval(timer);
    if (interval > 0 && !reduceMotion) timer = setInterval(() => show(index + 1), interval);
  }

  prev?.addEventListener('click', () => { show(index - 1); restart(); });
  next?.addEventListener('click', () => { show(index + 1); restart(); });

  carousel.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft') { show(index - 1); restart(); }
    if (event.key === 'ArrowRight') { show(index + 1); restart(); }
  });

  // Do not animate under someone's cursor or while they are reading a caption.
  carousel.addEventListener('mouseenter', () => timer && clearInterval(timer));
  carousel.addEventListener('mouseleave', restart);
  carousel.addEventListener('focusin', () => timer && clearInterval(timer));
  carousel.addEventListener('focusout', restart);

  // Swipe on touch devices.
  let startX = null;
  carousel.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; }, { passive: true });
  carousel.addEventListener('touchend', (e) => {
    if (startX === null) return;
    const dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 40) { show(dx < 0 ? index + 1 : index - 1); restart(); }
    startX = null;
  }, { passive: true });

  show(index);
  restart();
});
