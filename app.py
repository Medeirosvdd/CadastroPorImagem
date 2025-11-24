from flask import Flask, render_template, request, jsonify
from flask_cors import CORS 
import cv2
import easyocr
import numpy as np
import base64
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configurações
reader = easyocr.Reader(['pt'], gpu=False)
sala_atual = 'Sala 1'
gaveta_atual = 'Gaveta 1'

# Conexão com o banco
def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST'),
        database=os.environ.get('DB_NAME'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        port=os.environ.get('DB_PORT')
    )

# Inicializar banco
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Criar tabelas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS salas (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gavetas (
            id SERIAL PRIMARY KEY,
            sala_id INTEGER REFERENCES salas(id),
            numero VARCHAR(50) NOT NULL,
            nome VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(sala_id, numero)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pastas (
            id SERIAL PRIMARY KEY,
            gaveta_id INTEGER REFERENCES gavetas(id),
            nome_aluno VARCHAR(200) NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Inserir dados iniciais
    cur.execute("INSERT INTO salas (nome) VALUES ('Sala 1'), ('Sala 2'), ('Sala 3') ON CONFLICT (nome) DO NOTHING")
    
    salas_gavetas = {
        'Sala 1': ['Gaveta 1', 'Gaveta 2', 'Gaveta 3'],
        'Sala 2': ['Gaveta 1', 'Gaveta 2'],
        'Sala 3': ['Gaveta 1', 'Gaveta 2', 'Gaveta 3', 'Gaveta 4']
    }
    
    for sala, gavetas in salas_gavetas.items():
        cur.execute("SELECT id FROM salas WHERE nome = %s", (sala,))
        sala_id = cur.fetchone()[0]
        
        for gaveta in gavetas:
            cur.execute(
                "INSERT INTO gavetas (sala_id, numero, nome) VALUES (%s, %s, %s) ON CONFLICT (sala_id, numero) DO NOTHING",
                (sala_id, gaveta, gaveta)
            )
    
    conn.commit()
    cur.close()
    conn.close()

# Funções de processamento de imagem (mantenha as suas)
def preprocessar_imagem(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    return gray

def extrair_texto(imagem):
    try:
        resultado = reader.readtext(imagem, detail=0)
        texto = " ".join(resultado).strip()
        return texto
    except Exception as e:
        return f"Erro no OCR: {e}"

# Rotas
@app.route('/')
def index():
    return render_template('index.html', sala_atual=sala_atual, gaveta_atual=gaveta_atual)

@app.route('/get_salas')
def get_salas():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT s.nome as sala, g.nome as gaveta, 
               COALESCE(json_agg(p.nome_aluno) FILTER (WHERE p.nome_aluno IS NOT NULL), '[]') as pastas
        FROM salas s
        LEFT JOIN gavetas g ON s.id = g.sala_id
        LEFT JOIN pastas p ON g.id = p.gaveta_id
        GROUP BY s.nome, g.nome
        ORDER BY s.nome, g.nome
    """)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    salas_dict = {}
    for sala, gaveta, pastas in rows:
        if sala not in salas_dict:
            salas_dict[sala] = {}
        salas_dict[sala][gaveta] = pastas
    
    return jsonify({
        'salas': salas_dict,
        'sala_atual': sala_atual,
        'gaveta_atual': gaveta_atual
    })

@app.route('/set_sala_gaveta', methods=['POST'])
def set_sala_gaveta():
    global sala_atual, gaveta_atual
    data = request.get_json()
    sala_atual = data['sala']
    gaveta_atual = data['gaveta']
    return jsonify({'status': 'success'})

@app.route('/processar_imagem', methods=['POST'])
def processar_imagem():
    try:
        data = request.get_json()
        image_data = data['imagem']
        header, encoded = image_data.split(",", 1)
        binary_data = base64.b64decode(encoded)
        nparr = np.frombuffer(binary_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img_processada = preprocessar_imagem(img)
        nome_detectado = extrair_texto(img_processada)
        
        return jsonify({
            'success': True,
            'nome_detectado': nome_detectado,
            'sala_atual': sala_atual,
            'gaveta_atual': gaveta_atual
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/confirmar_nome', methods=['POST'])
def confirmar_nome():
    try:
        data = request.get_json()
        nome = data['nome']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT g.id FROM gavetas g 
            JOIN salas s ON g.sala_id = s.id 
            WHERE s.nome = %s AND g.nome = %s
        """, (sala_atual, gaveta_atual))
        
        gaveta_id = cur.fetchone()[0]
        
        cur.execute(
            "INSERT INTO pastas (gaveta_id, nome_aluno) VALUES (%s, %s)",
            (gaveta_id, nome)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Adicionado: {nome} -> {sala_atual}/{gaveta_atual}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    init_db()  # Inicializa o banco na primeira execução
    app.run(debug=True, host='0.0.0.0', port=5000)