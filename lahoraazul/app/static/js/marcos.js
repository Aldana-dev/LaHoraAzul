const carrusel = document.getElementById("carruselMarcos");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");
const gap = 30;

let imgs = carrusel.querySelectorAll("img");
const imgCount = imgs.length;

// Clonar imágenes para efecto infinito
function clonarImagenes() {
    imgs = carrusel.querySelectorAll("img");
    for (let i = 0; i < imgCount; i++) {
        const clone = imgs[i].cloneNode(true);
        carrusel.appendChild(clone);
    }
    for (let i = imgCount - 1; i >= 0; i--) {
        const clone = imgs[i].cloneNode(true);
        carrusel.insertBefore(clone, carrusel.firstChild);
    }
}
clonarImagenes();

const todasImgs = carrusel.querySelectorAll("img");

// Posición inicial: primer elemento original
let posicion = imgCount;

const contenedor = document.querySelector(".carrusel-contenedor");

// Configuración de tamaño
function getSizes() {
    const vw = window.innerWidth;
    let visibleCount = 3;
    let imgWidth = 345; // ancho fijo de tus imágenes
    let containerWidth;

    if (vw < 768) {
        // Mobile: se recortan los costados
        containerWidth = vw; // ocupamos todo el ancho visible
        imgWidth = 345; // ancho fijo
    } else {
        // Desktop: 3 imágenes completas
        containerWidth = visibleCount * (imgWidth + gap);
    }

    return { imgWidth, containerWidth, visibleCount };
}

let { imgWidth, containerWidth, visibleCount } = getSizes();

// Posicionar carrusel
function setPosition() {
    const offset = -posicion * (imgWidth + gap) + (contenedor.offsetWidth - imgWidth) / 2;
    carrusel.style.transition = "none";
    carrusel.style.transform = `translateX(${offset}px)`;
    contenedor.style.width = containerWidth + "px";
    actualizarCentro();
    actualizarTitulo();
}

// Actualizar imagen central
function actualizarCentro() {
    todasImgs.forEach(img => img.classList.remove("centro"));
    if (todasImgs[posicion]) {
        todasImgs[posicion].classList.add("centro");
    }
}

// Actualizar título
function actualizarTitulo() {
    const titulo = todasImgs[posicion]?.dataset.titulo || "";
    document.getElementById("titulo-marco").textContent = titulo;
}

// Mover carrusel
function mover(n) {
    posicion += n;
    carrusel.style.transition = "transform 0.4s ease";
    const offset = -posicion * (imgWidth + gap) + (contenedor.offsetWidth - imgWidth) / 2;
    carrusel.style.transform = `translateX(${offset}px)`;
    actualizarCentro();
    actualizarTitulo();

    carrusel.addEventListener("transitionend", () => {
        if (posicion >= imgCount * 2) {
            // saltar al primer original
            posicion = imgCount;
            setPosition();
        } else if (posicion < imgCount) {
            // saltar al último original
            posicion = imgCount * 2 - 1;
            setPosition();
        }
    }, { once: true });
}

// Botones
btnNext.addEventListener("click", () => mover(1));
btnPrev.addEventListener("click", () => mover(-1));

// Ajustar al redimensionar
window.addEventListener("resize", () => {
    const sizes = getSizes();
    imgWidth = sizes.imgWidth;
    containerWidth = sizes.containerWidth;
    visibleCount = sizes.visibleCount;
    setPosition();
});

// Inicializar carrusel
setPosition();
