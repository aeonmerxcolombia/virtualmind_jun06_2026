(function() {
    if (window.__tooltipsLoaded) return;
    window.__tooltipsLoaded = true;

    const tooltipDict = {
        // Perfil
        nombre: 'Nombre completo del usuario',
        email: 'Correo electrónico institucional',
        telefono: 'Número de teléfono de contacto',
        password: 'Contraseña (mínimo 8 caracteres)',
        confirm_password: 'Confirma la contraseña ingresada',
        foto_url: 'URL de la foto de perfil',
        foto: 'Selecciona una imagen para tu perfil',
        documento: 'Número de documento de identidad',
        direccion: 'Dirección de residencia',
        ciudad: 'Ciudad de residencia',
        pais: 'País de residencia',
        genero: 'Género del usuario',
        fecha_nacimiento: 'Fecha de nacimiento',
        biografia: 'Breve descripción o resumen profesional',
        linkedin: 'URL de tu perfil de LinkedIn',
        sitio_web: 'URL de tu sitio web personal o portafolio',

        // Proyectos
        nombre_proyecto: 'Nombre identificador del proyecto',
        descripcion: 'Descripción detallada del proyecto',
        descripcion_proyecto: 'Describe el propósito y alcance del proyecto',
        objetivo: 'Objetivo principal del proyecto',
        presupuesto: 'Presupuesto asignado al proyecto',
        fecha_inicio: 'Fecha en que inicia el proyecto',
        fecha_fin: 'Fecha estimada de finalización',
        fecha_limite: 'Fecha límite para completar la tarea',
        estado: 'Estado actual del proyecto o tarea',
        prioridad: 'Nivel de importancia: Alta, Media o Baja',
        categoria: 'Clasificación del tipo de trabajo',
        responsable: 'Persona encargada de ejecutar la tarea',
        asignado_a: 'Usuario al que se le asigna esta tarea',
        porcentaje: 'Porcentaje de avance (0-100)',
        archivo: 'Selecciona un archivo para subir',
        documento_subir: 'Sube el documento requerido',

        // Tareas
        titulo_tarea: 'Título descriptivo de la tarea',
        descripcion_tarea: 'Explica qué hay que hacer en esta tarea',
        tarea_descripcion: 'Describe en detalle la tarea a realizar',
        notas: 'Información adicional o comentarios',
        notas_adicionales: 'Contexto extra o requisitos específicos',
        horas_estimadas: 'Tiempo estimado en horas para completar',
        horas_reales: 'Tiempo real invertido',

        // Módulos / Unidades
        titulo_modulo: 'Nombre del módulo o unidad didáctica',
        descripcion_modulo: 'Contenido y objetivos del módulo',
        contenido: 'Material de contenido del módulo',
        duracion: 'Duración estimada en horas o semanas',
        orden: 'Posición en la secuencia del curso',
        recursos: 'Materiales adicionales o enlaces de apoyo',

        // Evaluaciones
        tipo_evaluacion: 'Tipo: Diagnóstica, Formativa o Sumativa',
        puntaje_maximo: 'Puntuación máxima posible',
        preguntas: 'Número de preguntas de la evaluación',
        tiempo_limite: 'Tiempo máximo en minutos para completar',
        criterios: 'Criterios de evaluación y calificación',

        // Cursos
        titulo_curso: 'Nombre del curso',
        descripcion_curso: 'Descripción general del curso',
        duracion_curso: 'Duración total del curso',
        nivel: 'Nivel de dificultad: Básico, Intermedio o Avanzado',
        modalidad: 'Presencial, Virtual o Mixta',
        instructor: 'Nombre del instructor o facilitador',

        // Clientes / CRM
        nombre_cliente: 'Nombre completo del cliente o empresa',
        empresa: 'Nombre de la empresa u organización',
        nit: 'NIT o identificación tributaria',
        tipo_cliente: 'Tipo de cliente: Potencial, Activo, Inactivo',
        fuente: 'Cómo se enteró del servicio',
        costo: 'Costo o valor del proyecto/servicio',
        fecha_contacto: 'Fecha del primer contacto',
        notas_cliente: 'Observaciones importantes sobre el cliente',

        // Plan de estudio
        nombre_plan: 'Nombre del plan de formación',
        descripcion_plan: 'Objetivos y contenido del plan',
        duracion_plan: 'Duración total en horas o meses',
        certificado: '¿El plan otorga certificación?',

        // Búsqueda
        busqueda: 'Escribe tu búsqueda aquí',
        buscar: 'Buscar en el sistema',
        filtro: 'Filtra los resultados por categoría',
        buscar_usuario: 'Buscar usuario por nombre o email',
        buscar_proyecto: 'Buscar proyecto por nombre o código',
        buscar_tarea: 'Buscar tarea por título o descripción',

        // Generales
        comentario: 'Escribe un comentario',
        mensaje: 'Escribe tu mensaje aquí',
        asunto: 'Asunto del mensaje o solicitud',
        titulo: 'Título descriptivo',
        url: 'URL del enlace',
        etiqueta: 'Etiqueta o palabra clave',
        tags: 'Palabras clave separadas por coma',
        observacion: 'Observación o comentario adicional',
        motivo: 'Razón o motivo de la solicitud',
        justificacion: 'Justificación detallada de la petición',

        // Cronograma
        nombre_actividad: 'Nombre de la actividad programada',
        fecha_programada: 'Fecha programada para la actividad',
        hora_inicio: 'Hora de inicio de la actividad',
        hora_fin: 'Hora de finalización de la actividad',
        lugar: 'Ubicación o lugar del evento',
        participantes: 'Personas que participan en la actividad',

        // Audio / Imagen / IA
        prompt: 'Instrucción clara para la IA: describe lo que necesitas generar',
        texto_a_generar: 'Texto base para la generación de audio',
        voz: 'Selecciona el tipo de voz para la narración',
        idioma: 'Idioma del contenido a generar',
        estilo: 'Estilo visual: Realista, Animado, Acuarela, etc.',
        tamano: 'Dimensiones de la imagen a generar',
        resolucion: 'Resolución del video o imagen',
        duracion_audio: 'Duración aproximada del audio en segundos',
        musica_fondo: 'Agregar música de fondo al audio',
        guion: 'Guion o texto para la locución',

        // Documentos
        titulo_documento: 'Nombre del documento',
        tipo_documento: 'Tipo: PDF, Word, Excel, Imagen, etc.',
        contenido_documento: 'Contenido del documento',
        editor_contenido: 'Área de edición de texto enriquecido',
        compartir_con: 'Usuarios con los que compartirás el documento',
        permiso_acceso: 'Nivel de permiso: Solo lectura, Edición, Comentario',
        version: 'Número de versión del documento',
        cambios: 'Descripción de los cambios realizados en esta versión'
    };

    function getLabelText(input) {
        const id = input.id;
        if (id) {
            const label = document.querySelector(`label[for="${id}"]`);
            if (label) return label.textContent.trim().replace('*', '').trim();
        }
        const parent = input.closest('.field, .form-group, div');
        if (parent) {
            const label = parent.querySelector('label');
            if (label) return label.textContent.trim().replace('*', '').trim();
        }
        return input.placeholder || input.name || id || '';
    }

    function addTooltip(input) {
        if (input.getAttribute('title')) return;

        const id = (input.id || '').toLowerCase();
        const name = (input.name || '').toLowerCase();
        const placeholder = (input.placeholder || '').toLowerCase();
        const labelText = getLabelText(input).toLowerCase();

        let tooltip = '';

        for (const [key, text] of Object.entries(tooltipDict)) {
            if (id.includes(key) || name.includes(key) || placeholder.includes(key) || labelText.includes(key)) {
                tooltip = text;
                break;
            }
        }

        if (!tooltip && placeholder) {
            tooltip = placeholder.charAt(0).toUpperCase() + placeholder.slice(1);
        }

        if (tooltip) {
            input.setAttribute('title', tooltip);
        }
    }

    function processInputs(root) {
        const selectors = 'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="file"]), textarea, select';
        const inputs = (root || document).querySelectorAll(selectors);
        inputs.forEach(addTooltip);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => processInputs());
    } else {
        processInputs();
    }

    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) {
                    if (node.matches && node.matches('input, textarea, select')) {
                        addTooltip(node);
                    } else if (node.querySelectorAll) {
                        processInputs(node);
                    }
                }
            });
        });
    });
    observer.observe(document.body || document.documentElement, { childList: true, subtree: true });
})();
