// Variáveis globais
let stream = null;
let currentSala = 'Sala 1';
let currentGaveta = 'Gaveta 1';
const API_BASE = 'http://127.0.0.1:5000'; // LINHA ADICIONADA

// Elementos DOM
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const btnCapturar = document.getElementById('btn-capturar');
const btnAtualizar = document.getElementById('btn-atualizar');
const salaSelect = document.getElementById('sala-select');
const gavetaSelect = document.getElementById('gaveta-select');
const modal = document.getElementById('modal-confirmacao');
const nomeInput = document.getElementById('nome-input');
const btnConfirmar = document.getElementById('btn-confirmar');
const btnRefazer = document.getElementById('btn-refazer');
const btnCancelar = document.getElementById('btn-cancelar');

// Inicialização
document.addEventListener('DOMContentLoaded', function () {
    iniciarCamera();
    carregarDados();
    configurarEventos();
});

async function iniciarCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 }
        });
        video.srcObject = stream;
    } catch (err) {
        console.error('Erro ao acessar a câmera:', err);
        alert('Não foi possível acessar a câmera. Verifique as permissões.');
    }
}

function configurarEventos() {
    btnCapturar.addEventListener('click', capturarImagem);
    btnAtualizar.addEventListener('click', atualizarSelecao);
    btnConfirmar.addEventListener('click', confirmarNome);
    btnRefazer.addEventListener('click', refazerCaptura);
    btnCancelar.addEventListener('click', fecharModal);

    salaSelect.addEventListener('change', atualizarGavetas);
}

async function carregarDados() {
    try {
        const response = await fetch(`${API_BASE}/get_salas`); // CORRIGIDO
        const data = await response.json();

        currentSala = data.sala_atual;
        currentGaveta = data.gaveta_atual;

        atualizarInterface(data);
        atualizarGavetas();
    } catch (error) {
        console.error('Erro ao carregar dados:', error);
    }
}

function atualizarInterface(data) {
    // Atualizar selects
    salaSelect.value = currentSala;

    // Atualizar status
    document.getElementById('status-sala').innerHTML = `Sala: <strong>${currentSala}</strong>`;
    document.getElementById('status-gaveta').innerHTML = `Gaveta: <strong>${currentGaveta}</strong>`;

    // Atualizar estatísticas
    atualizarEstatisticas(data);
}

function atualizarGavetas() {
    const sala = salaSelect.value;

    // Limpar gavetas
    gavetaSelect.innerHTML = '';

    // Adicionar gavetas baseadas na sala selecionada
    const gavetas = {
        'Sala 1': ['Gaveta 1', 'Gaveta 2', 'Gaveta 3'],
        'Sala 2': ['Gaveta 1', 'Gaveta 2'],
        'Sala 3': ['Gaveta 1', 'Gaveta 2', 'Gaveta 3', 'Gaveta 4']
    };

    gavetas[sala].forEach(gaveta => {
        const option = document.createElement('option');
        option.value = gaveta;
        option.textContent = gaveta;
        gavetaSelect.appendChild(option);
    });

    gavetaSelect.value = currentGaveta;
}

async function atualizarSelecao() {
    currentSala = salaSelect.value;
    currentGaveta = gavetaSelect.value;

    try {
        await fetch(`${API_BASE}/set_sala_gaveta`, { // CORRIGIDO
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sala: currentSala,
                gaveta: currentGaveta
            })
        });

        carregarDados();
    } catch (error) {
        console.error('Erro ao atualizar seleção:', error);
    }
}

function capturarImagem() {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL('image/jpeg');
    processarImagem(imageData);
}

async function processarImagem(imageData) {
    try {
        btnCapturar.disabled = true;
        btnCapturar.textContent = 'Processando...';

        const response = await fetch(`${API_BASE}/processar_imagem`, { // CORRIGIDO
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                imagem: imageData
            })
        });

        const data = await response.json();

        if (data.success) {
            abrirModal(data.nome_detectado);
        } else {
            alert('Erro ao processar imagem: ' + data.error);
        }

    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao processar imagem');
    } finally {
        btnCapturar.disabled = false;
        btnCapturar.textContent = '📸 Capturar Imagem';
    }
}

function abrirModal(nomeDetectado) {
    nomeInput.value = nomeDetectado;
    modal.style.display = 'block';
    nomeInput.focus();
}

function fecharModal() {
    modal.style.display = 'none';
    nomeInput.value = '';
}

async function confirmarNome() {
    const nome = nomeInput.value.trim();

    if (!nome) {
        alert('Por favor, digite um nome válido.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/confirmar_nome`, { // CORRIGIDO
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                nome: nome
            })
        });

        const data = await response.json();

        if (data.success) {
            alert(data.message);
            fecharModal();
            carregarDados();
        } else {
            alert('Erro ao confirmar nome: ' + data.error);
        }

    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao confirmar nome');
    }
}

function refazerCaptura() {
    fecharModal();
    // Foca na câmera para nova captura
    btnCapturar.focus();
}

function atualizarEstatisticas(data) {
    // Calcular progresso geral
    const totalGavetas = Object.values(data.salas).reduce((total, gavetas) =>
        total + Object.keys(gavetas).length, 0
    );

    const gavetasPreenchidas = Object.values(data.salas).reduce((total, gavetas) =>
        total + Object.values(gavetas).filter(pastas => pastas.length > 0).length, 0
    );

    document.getElementById('progresso-geral').textContent =
        `${gavetasPreenchidas}/${totalGavetas} gavetas`;

    // Contador da gaveta atual
    const pastasGavetaAtual = data.salas[currentSala][currentGaveta].length;
    document.getElementById('contador-gaveta').textContent =
        `${pastasGavetaAtual} pastas`;

    // Lista de pastas
    const listaPastas = document.getElementById('lista-pastas');
    listaPastas.innerHTML = '';

    data.salas[currentSala][currentGaveta].forEach((pasta, index) => {
        const div = document.createElement('div');
        div.className = 'pasta-item';
        div.textContent = `${index + 1}. ${pasta}`;
        listaPastas.appendChild(div);
    });

    if (pastasGavetaAtual === 0) {
        listaPastas.innerHTML = '<div class="pasta-item">Nenhuma pasta ainda</div>';
    }
}

// Fechar modal clicando fora
window.addEventListener('click', function (event) {
    if (event.target === modal) {
        fecharModal();
    }
});

// Teclas de atalho
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && modal.style.display === 'block') {
        fecharModal();
    }
});