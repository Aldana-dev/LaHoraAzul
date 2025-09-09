const modalEditar = document.getElementById("modal-editar");
const formEditar = document.getElementById("form-editar-producto");
const cerrarEditar = modalEditar.querySelector(".cerrar");
const imgPrincipalEdit = document.getElementById("img-principal-edit");
const imagenesAdicionalesEdit = document.getElementById(
    "imagenes-adicionales-edit"
);
const inputImagenesAEliminar = document.getElementById(
    "imagenes-a-eliminar"
);

function crearBotonEliminar(onClick) {
    const btnEliminar = document.createElement("button");
    btnEliminar.textContent = "✖";
    btnEliminar.type = "button";
    btnEliminar.title = "Eliminar imagen";
    btnEliminar.classList.add("btn-eliminar-imagen"); // Usar estilos en CSS
    btnEliminar.onclick = onClick;
    return btnEliminar;
}

function renderizarImagenesAdicionales(imagenes, contenedor, inputEliminar) {
    contenedor.innerHTML = "";

    imagenes.forEach(imgNombre => {
        const wrapper = document.createElement("div");
        wrapper.classList.add("contenedor-imagen-adicional");

        const img = document.createElement("img");
        img.src = `/static/${imgNombre}`;
        img.alt = "Imagen adicional";
        img.classList.add("imagen-adicional");

        const btnEliminar = crearBotonEliminar(() => {
            if (confirm("¿Eliminar esta imagen adicional?")) {
                wrapper.remove();
                const nombresAEliminar = inputEliminar.value
                    ? inputEliminar.value.split(",")
                    : [];
                nombresAEliminar.push(imgNombre);
                inputEliminar.value = nombresAEliminar.join(",");
            }
        });

        wrapper.appendChild(img);
        wrapper.appendChild(btnEliminar);
        contenedor.appendChild(wrapper);
    });
}
document.querySelectorAll(".edit-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        modalEditar.style.display = "block";
        inputImagenesAEliminar.value = "";

        document.getElementById("edit-id").value = btn.dataset.id;
        document.getElementById("edit-nombre").value = btn.dataset.nombre;
        document.getElementById("edit-precio").value = btn.dataset.precio;
        document.getElementById("edit-descripcion").value = btn.dataset.descripcion;
        document.getElementById("edit-categoria").value = btn.dataset.categoria;

        formEditar.action = `/admin/productos/editar/${btn.dataset.id}`;

        const imagenPrincipal = btn.dataset.imagen;
        imgPrincipalEdit.src = imagenPrincipal ? `/static/${imagenPrincipal}` : `/static/img/placeholder.png`;

        const imagenes = JSON.parse(btn.dataset.imagenes || "[]");
        renderizarImagenesAdicionales(imagenes, imagenesAdicionalesEdit, inputImagenesAEliminar);
    });
});

cerrarEditar.onclick = () => (modalEditar.style.display = "none");
window.onclick = (e) => {
    if (e.target == modalEditar) modalEditar.style.display = "none";
};

// Editor para agregar producto
const quill = new Quill("#editor-container", {
    theme: "snow",
    placeholder: "Escribí la descripción del producto...",
});

document
    .querySelector(".form-producto form")
    .addEventListener("submit", function () {
        const html = quill.root.innerHTML;
        document.getElementById("descripcion-hidden").value = html;
    });

// Editor para editar producto
const quillEdit = new Quill("#editor-container-edit", {
    theme: "snow",
    placeholder: "Editar descripción...",
});

// Al abrir el modal, insertar contenido actual en Quill
document.querySelectorAll(".edit-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
        // ...otros campos...

        const descripcion = btn.dataset.descripcion || "";
        quillEdit.root.innerHTML = descripcion;
    });
});

// Al enviar formulario de edición, pasar contenido Quill a campo oculto
document
    .getElementById("form-editar-producto")
    .addEventListener("submit", function () {
        const html = quillEdit.root.innerHTML;
        document.getElementById("edit-descripcion").value = html;
    });
