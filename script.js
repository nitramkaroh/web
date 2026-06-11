const navToggle = document.querySelector('.nav-toggle');
const nav = document.querySelector('.site-nav');

if (navToggle && nav) {
  navToggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('is-open');
    navToggle.setAttribute('aria-expanded', String(isOpen));
  });
}

const slides = [...document.querySelectorAll('.slide')];
const prevButton = document.querySelector('.carousel-control.prev');
const nextButton = document.querySelector('.carousel-control.next');
let currentSlide = 0;

function showSlide(index) {
  if (!slides.length) return;
  slides[currentSlide].classList.remove('is-active');
  currentSlide = (index + slides.length) % slides.length;
  slides[currentSlide].classList.add('is-active');
}

if (prevButton && nextButton && slides.length) {
  prevButton.addEventListener('click', () => showSlide(currentSlide - 1));
  nextButton.addEventListener('click', () => showSlide(currentSlide + 1));
}
