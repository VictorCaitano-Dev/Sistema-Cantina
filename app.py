from flask import Flask, render_template, request, redirect, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'cantina'


def conectar():
    return sqlite3.connect("cantina2.db")


# ---------------- HOME ----------------
@app.route('/')
def home():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM produtos")
    total_produtos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vendas")
    total_vendas = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(valor_total) FROM vendas")
    faturamento = cursor.fetchone()[0] or 0

    cursor.execute("""
        SELECT produtos.nome, SUM(vendas.quantidade)
        FROM vendas
        JOIN produtos ON vendas.produto_id = produtos.id
        GROUP BY produtos.id, produtos.nome
        ORDER BY SUM(vendas.quantidade) DESC
        LIMIT 1
    """)
    produto_mais_vendido = cursor.fetchone()

    cursor.execute("""
        SELECT nome, estoque
        FROM produtos
        WHERE estoque <= 5
        ORDER BY estoque ASC
    """)
    estoque_baixo = cursor.fetchall()

    conn.close()

    return render_template(
        'index.html',
        total_produtos=total_produtos,
        total_vendas=total_vendas,
        faturamento=faturamento,
        produto_mais_vendido=produto_mais_vendido,
        estoque_baixo=estoque_baixo
    )


# ---------------- PRODUTOS ----------------
@app.route('/produtos', methods=['GET', 'POST'])
def produtos():
    conn = conectar()
    cursor = conn.cursor()

    busca = request.args.get('busca', '')

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])

        cursor.execute("""
            INSERT INTO produtos (nome, preco, estoque)
            VALUES (?, ?, ?)
        """, (nome, preco, estoque))

        conn.commit()
        flash("Produto cadastrado com sucesso!")
        return redirect('/produtos')

    if busca:
        cursor.execute("""
            SELECT * FROM produtos
            WHERE nome LIKE ?
        """, ('%' + busca + '%',))
    else:
        cursor.execute("SELECT * FROM produtos")

    produtos = cursor.fetchall()
    conn.close()

    return render_template('produtos.html', produtos=produtos)


# ---------------- EXCLUIR PRODUTO ----------------
@app.route('/excluir_produto/<int:id>')
def excluir_produto(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM produtos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash("Produto excluído com sucesso!")
    return redirect('/produtos')


# ---------------- EDITAR PRODUTO ----------------
@app.route('/editar_produto/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])

        cursor.execute("""
            UPDATE produtos
            SET nome = ?, preco = ?, estoque = ?
            WHERE id = ?
        """, (nome, preco, estoque, id))

        conn.commit()
        conn.close()

        flash("Produto atualizado com sucesso!")
        return redirect('/produtos')

    cursor.execute("""
        SELECT * FROM produtos WHERE id = ?
    """, (id,))

    produto = cursor.fetchone()
    conn.close()

    return render_template('editar_produto.html', produto=produto)


# ---------------- VENDAS ----------------
@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    conn = conectar()
    cursor = conn.cursor()

    # ---------------- POST (REGISTRAR VENDA) ----------------
    if request.method == 'POST':
        try:
            produto_id = int(request.form['produto_id'])
            quantidade = int(request.form['quantidade'])
        except:
            flash("Dados inválidos")
            return redirect('/vendas')

        cursor.execute("""
            SELECT nome, preco, estoque
            FROM produtos
            WHERE id = ?
        """, (produto_id,))

        produto = cursor.fetchone()

        if not produto:
            flash("Produto não encontrado")
            return redirect('/vendas')

        nome, preco, estoque = produto

        if quantidade <= 0:
            flash("Quantidade inválida")
            return redirect('/vendas')

        if quantidade > estoque:
            flash(f"Estoque insuficiente (atual: {estoque})")
            return redirect('/vendas')

        total = preco * quantidade
        novo_estoque = estoque - quantidade

        # registrar venda
        cursor.execute("""
            INSERT INTO vendas (produto_id, quantidade, valor_total, data_venda)
            VALUES (?, ?, ?, datetime('now'))
        """, (produto_id, quantidade, total))

        # atualizar estoque
        cursor.execute("""
            UPDATE produtos
            SET estoque = ?
            WHERE id = ?
        """, (novo_estoque, produto_id))

        conn.commit()

        flash(f"Venda registrada: {quantidade}x {nome} - R$ {total:.2f}")
        return redirect('/vendas')

    # ---------------- GET (CARREGAR DADOS) ----------------

    cursor.execute("SELECT id, nome, estoque FROM produtos")
    produtos = cursor.fetchall()

    cursor.execute("""
        SELECT vendas.id, produtos.nome, vendas.quantidade, vendas.valor_total, vendas.data_venda
        FROM vendas
        JOIN produtos ON vendas.produto_id = produtos.id
        ORDER BY vendas.data_venda DESC
    """)
    vendas = cursor.fetchall()

    cursor.execute("SELECT COALESCE(SUM(valor_total), 0) FROM vendas")
    faturamento_total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vendas")
    total_vendas = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM vendas")
    total_itens = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "vendas.html",
        produtos=produtos,
        vendas=vendas,
        faturamento_total=faturamento_total,
        total_vendas=total_vendas,
        total_itens=total_itens
    )


# ---------------- RELATÓRIO ----------------
@app.route('/relatorio_vendas')
def relatorio_vendas():
    conn = conectar()
    cursor = conn.cursor()

    # 💰 TOTAL DO DIA (VALOR)
    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0)
        FROM vendas
        WHERE date(data_venda) = date('now')
    """)
    vendas_dia_total = cursor.fetchone()[0]

    # 📦 PRODUTOS VENDIDOS NO DIA
    cursor.execute("""
        SELECT 
            produtos.nome,
            SUM(vendas.quantidade) AS quantidade_total,
            SUM(vendas.valor_total) AS valor_total
        FROM vendas
        JOIN produtos ON vendas.produto_id = produtos.id
        WHERE date(vendas.data_venda) = date('now')
        GROUP BY produtos.nome
        ORDER BY quantidade_total DESC
    """)
    produtos_dia = cursor.fetchall()

    # 📅 TOTAL DO MÊS
    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0)
        FROM vendas
        WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
    """)
    vendas_mes = cursor.fetchone()[0]

    # 💰 TOTAL GERAL
    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0)
        FROM vendas
    """)
    vendas_total = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "relatorio_vendas.html",
        vendas_dia_total=vendas_dia_total,
        produtos_dia=produtos_dia,
        vendas_mes=vendas_mes,
        vendas_total=vendas_total
    )

if __name__ == '__main__':
    app.run(debug=True)