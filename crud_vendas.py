import os
import sqlite3

def conectar():
    caminho = os.path.abspath("cantina2.db")
    print("BANCO USADO PELO PYTHON:", caminho)
    return sqlite3.connect(caminho)


def registrar_venda():
    produto_id = int(input("Digite o ID do produto vendido: "))
    quantidade = int(input("Digite a quantidade vendida: "))

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT nome, preco, estoque
        FROM produtos
        WHERE id = ?
    """, (produto_id,))

    produto = cursor.fetchone()

    if produto is None:
        print("Produto não encontrado.")
        conn.close()
        return

    nome, preco, estoque = produto

    if quantidade <= 0:
        print("A quantidade precisa ser maior que zero.")
        conn.close()
        return

    if quantidade > estoque:
        print("Estoque insuficiente.")
        print(f"Estoque atual de {nome}: {estoque}")
        conn.close()
        return

    valor_total = preco * quantidade
    novo_estoque = estoque - quantidade

    cursor.execute("""
        INSERT INTO vendas (produto_id, quantidade, valor_total)
        VALUES (?, ?, ?)
    """, (produto_id, quantidade, valor_total))

    cursor.execute("""
        UPDATE produtos
        SET estoque = ?
        WHERE id = ?
    """, (novo_estoque, produto_id))

    conn.commit()
    conn.close()

    print("Venda registrada com sucesso!")
    print(f"Produto: {nome}")
    print(f"Quantidade: {quantidade}")
    print(f"Valor total: R$ {valor_total:.2f}")
    print(f"Estoque restante: {novo_estoque}")

def listar_vendas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            vendas.id,
            produtos.nome,
            vendas.quantidade,
            vendas.valor_total,
            vendas.data_venda
        FROM vendas
        JOIN produtos ON vendas.produto_id = produtos.id
        ORDER BY vendas.data_venda DESC
    """)

    vendas = cursor.fetchall()

    print("\n===== VENDAS =====\n")

    if len(vendas) == 0:
        print("Nenhuma venda registrada.")
    else:
        for venda in vendas:
            print(
                f"ID: {venda[0]} | "
                f"Produto: {venda[1]} | "
                f"Quantidade: {venda[2]} | "
                f"Total: R$ {venda[3]:.2f} | "
                f"Data: {venda[4]}"
            )

    conn.close()