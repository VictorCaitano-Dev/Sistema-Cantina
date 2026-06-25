import sqlite3

conn = sqlite3.connect('cantina2.db')
cursor = conn.cursor()

# ---------------- PRODUTOS ----------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    estoque INTEGER NOT NULL
)
''')

# ---------------- FUNCIONÁRIOS ----------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
)
''')

# ---------------- VENDAS (SÓ CRIA UMA VEZ) ----------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS vendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_id INTEGER,
    quantidade INTEGER,
    valor_total REAL,
    data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_venda TEXT DEFAULT 'NORMAL',
    funcionario_nome TEXT,
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
)
''')

# ---------------- CAIXA ----------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS caixas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_abertura TEXT,
    data_fechamento TEXT,
    valor_inicial REAL NOT NULL,
    valor_vendido REAL DEFAULT 0,
    status TEXT DEFAULT 'ABERTO'
)
""")

# ---------------- NOVAS COLUNAS DE PAGAMENTO ----------------

try:
    cursor.execute("""
        ALTER TABLE vendas
        ADD COLUMN forma_pagamento TEXT
    """)
except:
    pass

try:
    cursor.execute("""
        ALTER TABLE vendas
        ADD COLUMN valor_recebido REAL
    """)
except:
    pass

try:
    cursor.execute("""
        ALTER TABLE vendas
        ADD COLUMN troco REAL
    """)
except:
    pass
conn.commit()
conn.close()

print("Banco criado/verificado com sucesso!")