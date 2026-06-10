(function() {
    if (window.vozInputInicializado) return;
    window.vozInputInicializado = true;

    const API_WHISPER = `https://gestordecursos.pegui.edu.co:8000/whisper/transcribir`;
    let mediaRecorder = null;
    let audioChunks = [];
    let campoActivo = null;

    const estilos = document.createElement('style');
    estilos.textContent = `
        .vm-mic-wrapper { display: inline-flex; align-items: center; gap: 4px; }
        .vm-mic-btn {
            display: inline-flex; align-items: center; justify-content: center;
            width: 36px; height: 36px; border-radius: 8px;
            background: #f3f4f6; border: 1px solid #d1d5db;
            color: #6b7280; cursor: pointer; transition: all 0.2s;
            flex-shrink: 0;
        }
        .vm-mic-btn:hover { background: #e0e7ff; color: #4f46e5; border-color: #4f46e5; }
        .vm-mic-btn.recording {
            background: #fee2e2; color: #dc2626; border-color: #dc2626;
            animation: vm-mic-pulse 1s infinite ease-in-out;
        }
        .vm-mic-btn.processing { background: #fef3c7; color: #d97706; border-color: #d97706; }
        .vm-mic-tooltip {
            position: absolute; background: #1f2937; color: white;
            padding: 4px 8px; border-radius: 6px; font-size: 11px;
            white-space: nowrap; z-index: 9999; pointer-events: none;
            transform: translateY(-100%); margin-top: -8px;
        }
        @keyframes vm-mic-pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
    `;
    document.head.appendChild(estilos);

    function getToken() { return localStorage.getItem('token'); }

    function agregarBotonMic(input) {
        if (input.dataset.vmMic) return;
        if (input.type === 'hidden' || input.type === 'submit' || input.type === 'button' || input.type === 'checkbox' || input.type === 'radio' || input.type === 'file' || input.type === 'password') return;
        if (input.readOnly || input.disabled) return;

        input.dataset.vmMic = 'true';
        const id = input.id || `vm-mic-${Math.random().toString(36).slice(2, 8)}`;
        if (!input.id) input.id = id;

        const wrapper = document.createElement('span');
        wrapper.className = 'vm-mic-wrapper';
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'vm-mic-btn';
        btn.innerHTML = '<i class="fas fa-microphone"></i>';
        btn.title = 'Grabar con voz';
        btn.dataset.campo = id;
        btn.onclick = function(e) {
            e.preventDefault();
            gestionarGrabacionWhisper(id);
        };
        wrapper.appendChild(btn);
    }

    function inicializar() {
        document.querySelectorAll('input[type="text"], input[type="email"], input[type="search"], input[type="url"], input[type="tel"], textarea').forEach(agregarBotonMic);
        const observer = new MutationObserver(() => {
            document.querySelectorAll('input[type="text"]:not([data-vm-mic]), input[type="email"]:not([data-vm-mic]), input[type="search"]:not([data-vm-mic]), input[type="url"]:not([data-vm-mic]), input[type="tel"]:not([data-vm-mic]), textarea:not([data-vm-mic])').forEach(agregarBotonMic);
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    async function gestionarGrabacionWhisper(idCampo) {
        const btn = document.querySelector(`.vm-mic-btn[data-campo="${idCampo}"]`);
        const ico = btn ? btn.querySelector('i') : null;

        if (mediaRecorder && mediaRecorder.state === "recording" && campoActivo === idCampo) {
            mediaRecorder.stop();
            return;
        }
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
        }

        campoActivo = idCampo;
        audioChunks = [];

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) audioChunks.push(e.data);
            };

            mediaRecorder.onstart = () => {
                resetearTodosMics();
                if (btn) btn.classList.add('recording');
                if (ico) { ico.className = 'fas fa-stop'; }
                setTimeout(() => {
                    if (mediaRecorder && mediaRecorder.state === "recording") mediaRecorder.stop();
                }, 10000);
            };

            mediaRecorder.onstop = async () => {
                if (btn) { btn.classList.remove('recording'); btn.classList.add('processing'); }
                if (ico) { ico.className = 'fas fa-spinner fa-spin'; }
                const audioBlob = new Blob(audioChunks, { type: 'audio/ogg' });
                stream.getTracks().forEach(track => track.stop());
                await enviarAudioAWhisper(audioBlob, idCampo);
            };

            mediaRecorder.start();
        } catch (err) {
            console.error("Error micrófono:", err);
            resetearTodosMics();
        }
    }

    async function enviarAudioAWhisper(blob, idCampo) {
        const token = getToken();
        const formData = new FormData();
        formData.append('audio', blob, 'dictado_voz.ogg');

        try {
            const res = await fetch(API_WHISPER, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData
            });
            if (!res.ok) throw new Error("Error en Whisper");
            const data = await res.json();
            const texto = (data.texto || '').trim();
            if (texto) {
                const input = document.getElementById(idCampo);
                if (input) {
                    input.value = input.value.trim() ? input.value.trim() + ' ' + texto : texto;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        } catch (err) {
            console.error("Error Whisper:", err);
        } finally {
            resetearTodosMics();
        }
    }

    function resetearTodosMics() {
        document.querySelectorAll('.vm-mic-btn').forEach(btn => {
            btn.className = 'vm-mic-btn';
            const ico = btn.querySelector('i');
            if (ico) ico.className = 'fas fa-microphone';
        });
        campoActivo = null;
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }
})();
