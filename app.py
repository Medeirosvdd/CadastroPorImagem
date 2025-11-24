from flask import Flask, render_template, request, jsonify
from flask_cors import CORS 
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configurações
sala_atual = 'Sala 1'
gaveta_atual = 'Gaveta 1'

# Usar SQLite temporariamente
def get_db_connection():
    conn = sqlite3.connect('pastas.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS salas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS gavetas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sala_id INTEGER,
                numero TEXT NOT NULL,
                nome TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sala_id) REFERENCES salas (id),
                UNIQUE(sala_id, numero)
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pastas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gaveta_id INTEGER,
                nome_aluno TEXT NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (gaveta_id) REFERENCES gavetas (id)
            )
        """)
        
        # Inserir dados iniciais
        cur.execute("INSERT OR IGNORE INTO salas (nome) VALUES ('Sala 1'), ('Sala 2'), ('Sala 3')")
        
        salas_gavetas = {
            'Sala 1': ['Gaveta 1', 'Gaveta 2', 'Gaveta 3'],
            'Sala 2': ['Gaveta 1', 'Gaveta 2'],
            'Sala 3': ['Gaveta 1', 'Gaveta 2', 'Gaveta 3', 'Gaveta 4']
        }
        
        for sala, gavetas in salas_gavetas.items():
            cur.execute("SELECT id FROM salas WHERE nome = ?", (sala,))
            sala_id = cur.fetchone()[0]
            
            for gaveta in gavetas:
                cur.execute(
                    "INSERT OR IGNORE INTO gavetas (sala_id, numero, nome) VALUES (?, ?, ?)",
                    (sala_id, gaveta, gaveta)
                )
        
        conn.commit()
        conn.close()
        print("✅ Banco SQLite inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")

# Função de OCR SIMULADA
def extrair_texto(imagem_data):
    nomes_simulados = ["João Silva", "Maria Santos", "Pedro Costa", "Ana Oliveira"]
    import random
    return random.choice(nomes_simulados)

# Rota PRINCIPAL - esta deve funcionar primeiro
@app.route('/')
def index():
    return render_template('index.html', sala_atual=sala_atual, gaveta_atual=gaveta_atual)

# Rota para pegar dados das salas
@app.route('/get_salas', methods=['GET'])
def get_salas():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT s.nome as sala, g.nome as gaveta, 
                   (SELECT GROUP_CONCAT(nome_aluno) 
                    FROM pastas p 
                    WHERE p.gaveta_id = g.id) as pastas
            FROM salas s
            LEFT JOIN gavetas g ON s.id = g.sala_id
            ORDER BY s.nome, g.nome
        """)
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        salas_dict = {}
        for row in rows:
            sala = row['sala']
            gaveta = row['gaveta']
            pastas = row['pastas'] or ""
            
            if sala not in salas_dict:
                salas_dict[sala] = {}
            
            # Converter string para lista
            if pastas:
                salas_dict[sala][gaveta] = pastas.split(',')
            else:
                salas_dict[sala][gaveta] = []
        
        return jsonify({
            'salas': salas_dict,
            'sala_atual': sala_atual,
            'gaveta_atual': gaveta_atual
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        nome_detectado = extrair_texto(None)
        
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
            WHERE s.nome = ? AND g.nome = ?
        """, (sala_atual, gaveta_atual))
        
        result = cur.fetchone()
        if not result:
            return jsonify({'success': False, 'error': 'Gaveta não encontrada'})
            
        gaveta_id = result['id']
        
        cur.execute(
            "INSERT INTO pastas (gaveta_id, nome_aluno) VALUES (?, ?)",
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
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)