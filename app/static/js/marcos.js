const carrusel = document.getElementById("carruselMarcos");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");
const gap = 30;

let imgs = carrusel.querySelectorAll("img");
const imgCount = imgs.length;

function clonarImagenes() {
    imgs = carrusel.querySelectorAll("img");
    for (let i = 0; i < imgCount; i++) {
        let clone = imgs[i].cloneNode(true);
        carrusel.appendChild(clone);
    }
    for (let i = imgCount - 1; i >= 0; i--) {
        let clone = imgs[i].cloneNode(true);
        carrusel.insertBefore(clone, carrusel.firstChild);
    }
}
clonarImagenes();

const todasImgs = carrusel.querySelectorAll("img");
let posicion = imgCount;

function getSizes(gap = 10) {
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

function setPosition() {
    const offset = -posicion * (imgWidth + gap);
    carrusel.style.transition = "none";
    carrusel.style.transform = `translateX(${offset}px)`;
    contenedor.style.width = containerWidth + "px"; // ajusto contenedor
    actualizarCentro();
    actualizarTitulo();
}

function actualizarCentro() {
    todasImgs.forEach((img) => img.classList.remove("centro"));
    const indexCentro = posicion + 1;
    if (todasImgs[indexCentro]) {
        todasImgs[indexCentro].classList.add("centro");
    }
}

function actualizarTitulo() {
    const titulo = todasImgs[posicion]?.dataset.titulo || "";
    document.getElementById("titulo-marco").textContent = titulo;
}

function mover(n) {
    posicion += n;
    carrusel.style.transition = "transform 0.4s ease";
    const offset = -posicion * (imgWidth + gap);
    carrusel.style.transform = `translateX(${offset}px)`;
    actualizarCentro();
    actualizarTitulo();

    carrusel.addEventListener(
        "transitionend",
        () => {
            if (posicion >= imgCount * 2) {
                posicion = imgCount;
                carrusel.style.transition = "none";
                setPosition();
            } else if (posicion < imgCount) {
                posicion = imgCount * 2 - 1;
                carrusel.style.transition = "none";
                setPosition();
            }
        },
        { once: true }
    );
}

btnNext.addEventListener("click", () => mover(1));
btnPrev.addEventListener("click", () => mover(-1));

window.addEventListener("resize", () => {
    const sizes = getSizes();
    imgWidth = sizes.imgWidth;
    containerWidth = sizes.containerWidth;
    visibleCount = sizes.visibleCount;
    setPosition();
});

setPosition();
