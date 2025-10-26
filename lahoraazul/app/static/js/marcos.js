const images = [
  '/static/img/marcos/doble_vidrio.jpg',
  '/static/img/marcos/marco_directo_1.jpg',
  '/static/img/marcos/marco_directo_2.jpg',
  '/static/img/marcos/marco_directo_3.jpg',
  '/static/img/marcos/marco_directo_4.jpg',
  '/static/img/marcos/passepartout_1.jpg',
  '/static/img/marcos/passepartout_2.jpg',
  '/static/img/marcos/varillas_pintadas.jpg'
];

let currentIndex = 1;
const frames = document.querySelectorAll('.frame img');
const btnPrev = document.getElementById('btn-prev');
const btnNext = document.getElementById('btn-next');
const tituloMarco = document.getElementById('titulo-marco');

function updateCarousel() {
  const leftIndex = (currentIndex - 1 + images.length) % images.length;
  const centerIndex = currentIndex;
  const rightIndex = (currentIndex + 1) % images.length;

  frames[0].src = images[leftIndex];
  frames[1].src = images[centerIndex];
  frames[2].src = images[rightIndex];

  preloadImage(images[leftIndex]);
  preloadImage(images[rightIndex]);

  const titulo = images[centerIndex].split('/').pop().replace('.jpg', '').replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  tituloMarco.textContent = titulo;
}

function preloadImage(src) {
  const img = new Image();
  img.src = src;
}

btnNext.addEventListener('click', () => {
  currentIndex = (currentIndex + 1) % images.length;
  updateCarousel();
});

btnPrev.addEventListener('click', () => {
  currentIndex = (currentIndex - 1 + images.length) % images.length;
  updateCarousel();
});

// Gestos Táctiles (Swipe)
let startX = 0;
let endX = 0;

document.querySelector('.frames').addEventListener('touchstart', (e) => {
  startX = e.touches[0].clientX;
});

document.querySelector('.frames').addEventListener('touchend', (e) => {
  endX = e.changedTouches[0].clientX;
  if (startX - endX > 50) btnNext.click();
  if (endX - startX > 50) btnPrev.click();
});

// Gestos de Ratón (Drag/Scroll Horizontal)
let isDragging = false;
let startDragX = 0;

document.querySelector('.frames').addEventListener('mousedown', (e) => {
  isDragging = true;
  startDragX = e.clientX;
});

document.querySelector('.frames').addEventListener('mousemove', (e) => {
  if (!isDragging) return;
  const deltaX = e.clientX - startDragX;
  if (deltaX > 50) {
    btnPrev.click();
    isDragging = false;
  } else if (deltaX < -50) {
    btnNext.click();
    isDragging = false;
  }
});

document.querySelector('.frames').addEventListener('mouseup', () => {
  isDragging = false;
});

// Función de throttling para limitar frecuencia
function throttle(func, limit) {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

// Scroll horizontal con throttling (500ms de delay)
document.querySelector('.frames').addEventListener('wheel', throttle((e) => {
  e.preventDefault();
  if (e.deltaX > 0) btnNext.click();
  else btnPrev.click();
}, 500));

// Inicializar
updateCarousel();