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
  if (slides.length === 1) {
    carousel.classList.add('is-single');
    slides[0].classList.add('is-active');
    return;
  }

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
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
