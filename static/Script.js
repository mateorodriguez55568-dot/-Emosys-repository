let mostrarTodo = false;
let todosLosRegistros = [];

// 1. Formatear Fecha y Hora exacta
function formatearFechaHora(fechaStr) {
    if (!fechaStr) return "Sin fecha";
    // Python envía el formato ISO: "2024-11-25T14:32:05"
    const fecha = new Date(fechaStr);
    const dias = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    const meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
    
    let diaSemana = dias[fecha.getDay()];
    let dia = fecha.getDate();
    let mes = meses[fecha.getMonth()];
    let anio = fecha.getFullYear();
    let horas = fecha.getHours().toString().padStart(2, '0');
    let minutos = fecha.getMinutes().toString().padStart(2, '0');
    let segundos = fecha.getSeconds().toString().padStart(2, '0');

    return `${diaSemana}, ${dia} de ${mes} de ${anio} - ${horas}:${minutos}:${segundos}`;
}

// 2. Cargar Historial Usuarios
async function cargarHistorialBD() {
    const listaUI = document.getElementById('lista-global-usuarios');
    const btnMas = document.getElementById('btn-mostrar-mas');
    const btnVolver = document.getElementById('btn-volver');
    if (!listaUI) return;

    try {
        // Ruta de Flask
        const res = await fetch("/api/usuarios");

if (!res.ok) throw new Error("Error al obtener usuarios");

todosLosRegistros = await res.json();
    } catch (err) {
        console.error("Error al cargar registros:", err); return;
    }

    listaUI.innerHTML = "";
    if (todosLosRegistros.length === 0) {
        listaUI.innerHTML = "<p style='opacity:0.5; font-size:0.9rem;'>No hay registros aún.</p>";
        if (btnMas) btnMas.style.display = "none";
        if (btnVolver) btnVolver.style.display = "none";
        return;
    }

    const copiaDatos = [...todosLosRegistros].reverse();
    const registrosAExhibir = mostrarTodo ? copiaDatos : copiaDatos.slice(0, 5);

    registrosAExhibir.forEach(user => {
        const li = document.createElement('li');
        li.style.padding = "15px"; li.style.borderBottom = "1px solid rgba(255,255,255,0.1)";
        li.style.listStyle = "none"; li.style.textAlign = "left"; li.style.fontSize = "0.85rem";
        let fechaExacta = formatearFechaHora(user.fecha_registro);

        li.innerHTML = `
            <div style="color: #00d2ff; font-weight: 600; margin-bottom: 5px;">
                ✅ ${user.nombres_apellidos ? user.nombres_apellidos.toUpperCase() : 'ANÓNIMO'}
            </div>
            <div style="opacity: 0.8; color: white;">
                <span>📅 <strong>Registrado:</strong> ${fechaExacta}</span><br>
                <span>🎂 <strong>Edad:</strong> ${user.edad || '--'} años</span> | 
                <span>👤 <strong>Tipo:</strong> ${user.tipo_usuario || '--'}</span>
            </div>
        `;
        listaUI.appendChild(li);
    });

    if (todosLosRegistros.length > 5) {
        if (mostrarTodo) { btnMas.style.display = "none"; btnVolver.style.display = "flex"; }
        else { btnMas.style.display = "flex"; btnVolver.style.display = "none"; }
    } else { btnMas.style.display = "none"; btnVolver.style.display = "none"; }
}

// 3. Botones
function verMas() { mostrarTodo = true; cargarHistorialBD(); }
function volverAlInicio() { mostrarTodo = false; cargarHistorialBD(); document.getElementById('historial-global').scrollIntoView({ behavior: 'smooth' }); }

// 4. Registro
const formRegistro = document.getElementById('form-registro');
if (formRegistro) {
    formRegistro.addEventListener('submit', async function (e) {
        e.preventDefault();
        
        // Se envía como JSON a Python
        const data = {
            cedula: document.getElementById('cedula').value.trim(),
            nombres: document.getElementById('nombres').value.trim(),
            edad: parseInt(document.getElementById('edad').value),
            email: document.getElementById('email').value.trim(),
            tipo_usuario: document.getElementById('tipo-usuario').value
        };

        try {
            const res = await fetch("/api/registrar", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
});

const datos = await res.json();

if (res.ok && datos.exito) {

    localStorage.setItem("usuarioActual", JSON.stringify(datos.usuario));
    localStorage.setItem("sistemaActivo", "true");

    window.location.href = "/Monitor";

} else {

    notificar("❌ " + (datos.error || "Error al registrar"), "error");

}
        } catch (err) { notificar("❌ Error de conexión con el servidor", "error"); }
    });
}

// 5. Limpiar
function limpiarHistorial() {
    if (!confirm("¿Seguro borras todo? Se eliminarán todos los registros y comentarios.")) return;
    fetch("/api/limpiar", {
    method: "DELETE"
})
        .then(res => res.json())
        .then(datos => {
            if (datos.exito) { notificar("🗑️ " + datos.mensaje, "exito"); mostrarTodo = false; cargarHistorialBD(); cargarComentariosBD(); }
            else { notificar("❌ " + (datos.error || "Error al eliminar"), "error"); }
        }).catch(() => notificar("❌ Error de conexión", "error"));
}

// 6. Comentarios
async function cargarComentariosBD() {
    const listaUI = document.getElementById('lista-comentarios');
    if (!listaUI) return;
    try {
        const res = await fetch("/api/comentarios");

if (!res.ok) throw new Error("Error al obtener comentarios");
        const comentarios = await res.json();
        listaUI.innerHTML = "";
        if (comentarios.length === 0) { listaUI.innerHTML = "<p style='opacity:0.5; font-size:0.9rem;'>No hay comentarios aún.</p>"; return; }
        comentarios.forEach(c => {
            const li = document.createElement('li');
            li.style.padding = "15px"; li.style.borderBottom = "1px solid rgba(255,255,255,0.1)";
            li.style.listStyle = "none"; li.style.textAlign = "left"; li.style.fontSize = "0.85rem";
            let fechaExacta = formatearFechaHora(c.fecha_comentario);
            li.innerHTML = `
                <div style="color: #10b981; font-weight: 600; margin-bottom: 5px;">💬 ${c.nombre_usuario.toUpperCase()}</div>
                <div style="opacity: 0.9; color: white; margin-bottom: 5px;">${c.comentario}</div>
                <div style="opacity: 0.5; font-size: 0.8rem; color: #ccc;">🕒 ${fechaExacta}</div>
            `;
            listaUI.appendChild(li);
        });
    } catch (err) { console.error("Error al cargar comentarios:", err); }
}

const formComentario = document.getElementById('form-comentario');
if (formComentario) {
    window.addEventListener('load', () => {
        const u = JSON.parse(localStorage.getItem('usuarioActual'));
        if (u && u.nombre) document.getElementById('comentario-nombre').value = u.nombre;
    });
    formComentario.addEventListener('submit', async function (e) {
        e.preventDefault();
        const u = JSON.parse(localStorage.getItem('usuarioActual'));
        
        const data = {
            cedula: (u && u.cedula) ? u.cedula : "",
            nombre: document.getElementById('comentario-nombre').value.trim(),
            comentario: document.getElementById('comentario-texto').value.trim()
        };

        try {
            const res = await fetch("/api/comentar", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
});
            const datos = await res.json();
            if (datos.exito) { notificar("✅ Comentario enviado", "exito"); document.getElementById('comentario-texto').value = ''; cargarComentariosBD(); }
            else { notificar("❌ " + (datos.error || "Error al enviar"), "error"); }
        } catch (err) { notificar("❌ Error de conexión", "error"); }
    });
}

// 7. Inicio y Utilidad
window.addEventListener('load', function () { cargarHistorialBD(); cargarComentariosBD(); });

function notificar(mensaje, tipo) {
    const existente = document.querySelector(".notificacion-db");
    if (existente) existente.remove();
    const div = document.createElement("div");
    div.className = "notificacion-db " + tipo;
    div.textContent = mensaje;
    document.body.appendChild(div);
    setTimeout(() => { div.style.opacity = "0"; div.style.transition = "0.4s"; setTimeout(() => div.remove(), 400); }, 3500);
}
// ============================================
// FINALIZAR MONITOREO Y ENVIAR CORREO
// ============================================

async function finalizarMonitoreo(){

    const usuario = JSON.parse(
        localStorage.getItem("usuarioActual")
    );


    if(!usuario){
        notificar(
            "❌ No existe usuario registrado",
            "error"
        );
        return;
    }


    // Aquí tomas los datos de tus sensores
    const datos = {

        nombre: usuario.nombre,

        email: usuario.email,

        temperatura: window.temperaturaActual || 0,

        pulso: window.pulsoActual || 0,

        emocion: window.emocionActual || "No detectada"

    };


    try{


        const respuesta = await fetch(
            "/api/finalizar_monitoreo",
            {
                method:"POST",

                headers:{
                    "Content-Type":"application/json"
                },

                body: JSON.stringify(datos)
            }
        );


        const resultado = await respuesta.json();


        if(respuesta.ok && resultado.exito){


            notificar(
                "✅ Correo enviado correctamente",
                "exito"
            );


        }else{


            notificar(
                "❌ "+resultado.mensaje,
                "error"
            );

        }



    }catch(error){

        console.error(
            "ERROR FLASK:",
            error
        );


        notificar(
            "❌ No se pudo conectar con Flask",
            "error"
        );

    }

}

    // Función que rellena automáticamente el campo
    function rellenarNombreComentario() {
        // 1. Buscamos el campo de comentarios
        const campoNombre = document.getElementById('comentario-nombre');
        
        // 2. Buscamos el nombre que se escribió en el formulario de registro
        const nombreRegistrado = document.getElementById('nombres').value;

        // 3. Si el campo existe y hay un nombre escrito, lo ponemos ahí
        if (campoNombre && nombreRegistrado.trim() !== "") {
            campoNombre.value = nombreRegistrado;
            // Quitamos el placeholder gris de "Regístrate arriba..."
            campoNombre.placeholder = ""; 
        }
    }
    document.getElementById('nombres').addEventListener('input', rellenarNombreComentario);

    document.getElementById('form-registro').addEventListener('submit', function() {
        setTimeout(rellenarNombreComentario, 100); // Pequeña pausa para asegurar que tome el dato
    });

    document.getElementById('form-comentario').addEventListener('submit', function(e) {
        e.preventDefault(); // Evita que la página recargue
        
        const nombre = document.getElementById('comentario-nombre').value;
        const texto = document.getElementById('comentario-texto').value;

        if (texto.trim() !== "") {
            const lista = document.getElementById('lista-comentarios');
            const li = document.createElement('li');
            li.style.marginBottom = "10px";
            li.innerHTML = `<strong>${nombre}:</strong> ${texto}`;
            
            // Agrega el comentario nuevo arriba del todo
            lista.insertBefore(li, lista.firstChild);
            
            // Limpia solo el cuadro del comentario, el nombre se queda guardado
            document.getElementById('comentario-texto').value = '';
        }
    });
