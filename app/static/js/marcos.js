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
let posicion = imgCount;

// Configuración responsive
function getSizes() {
    const vw = window.innerWidth;
    const config = [
        { max: 480, imgWidth: vw - gap, containerWidth: vw, visibleCount: 1 },
        { max: 768, imgWidth: 160, containerWidth: 160 + gap, visibleCount: 1 },
        { max: Infinity, imgWidth: 300, containerWidth: 960, visibleCount: 3 },
    ];
    return config.find(c => vw <= c.max);
}

let { imgWidth, containerWidth, visibleCount } = getSizes();

const contenedor = document.querySelector(".carrusel-contenedor");

// Posicionar carrusel
function setPosition() {
    const offset = -posicion * (imgWidth + gap);
    carrusel.style.transition = "none";
    carrusel.style.transform = `translateX(${offset}px)`;
    contenedor.style.width = containerWidth + "px";
    actualizarCentro();
    actualizarTitulo();
}

// Actualizar imagen central
function actualizarCentro() {
    todasImgs.forEach(img => img.classList.remove("centro"));
    const centroIndex = posicion + Math.floor(visibleCount / 2);
    if (todasImgs[centroIndex]) {
        todasImgs[centroIndex].classList.add("centro");
    }
}

// Actualizar título
function actualizarTitulo() {
    const centroIndex = posicion + Math.floor(visibleCount / 2);
    const titulo = todasImgs[centroIndex]?.dataset.titulo || "";
    document.getElementById("titulo-marco").textContent = titulo;
}

// Mover carrusel
function mover(n) {
    posicion += n;
    carrusel.style.transition = "transform 0.4s ease";
    const offset = -posicion * (imgWidth + gap);
    carrusel.style.transform = `translateX(${offset}px)`;
    actualizarCentro();
    actualizarTitulo();

    carrusel.addEventListener("transitionend", () => {
        if (posicion >= imgCount * 2) {
            posicion = imgCount;
            setPosition();
        } else if (posicion < imgCount) {
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

setPosition();
