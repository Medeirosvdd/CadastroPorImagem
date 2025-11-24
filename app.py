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

# ... o resto do código igual ...

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)