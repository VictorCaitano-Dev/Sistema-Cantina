from flask import Flask, render_template, request, redirect, flash
from datetime import datetime
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

    # CAIXA ABERTO
    cursor.execute("""
        SELECT *
        FROM caixas
        WHERE status = 'ABERTO'
        ORDER BY id DESC
        LIMIT 1
    """)
    caixa_aberto = cursor.fetchone()

    total_caixa = 0

    if caixa_aberto:
        cursor.execute("""
            SELECT COALESCE(SUM(valor_total), 0)
            FROM vendas
            WHERE date(data_venda) = date('now')
        """)
        total_caixa = cursor.fetchone()[0]

    conn.close()

    return render_template(
        'index.html',
        total_produtos=total_produtos,
        total_vendas=total_vendas,
        faturamento=faturamento,
        produto_mais_vendido=produto_mais_vendido,
        estoque_baixo=estoque_baixo,
        caixa_aberto=caixa_aberto,
        total_caixa=total_caixa
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

    # ---------------- POST ----------------
    if request.method == 'POST':

        produto_id = request.form.get('produto_id')
        quantidade = request.form.get('quantidade')

        tipo_venda = request.form.get('tipo_venda')
        funcionario_nome = request.form.get('funcionario_nome')

        forma_pagamento = request.form.get('forma_pagamento')
        valor_recebido = request.form.get('valor_recebido')

        if not produto_id or not quantidade:
            flash("Dados inválidos")
            return redirect('/vendas')

        produto_id = int(produto_id)
        quantidade = int(quantidade)

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
            flash("Estoque insuficiente")
            return redirect('/vendas')

        # valida funcionário no fiado
        if tipo_venda == "FIADO" and not funcionario_nome:
            flash("Selecione um funcionário para venda fiado")
            return redirect('/vendas')

        total = preco * quantidade

        troco = None

        # venda normal
        if tipo_venda == "NORMAL":

            if not forma_pagamento:
                flash("Selecione a forma de pagamento")
                return redirect('/vendas')

            if forma_pagamento == "DINHEIRO":

                if not valor_recebido:
                    flash("Informe o valor recebido")
                    return redirect('/vendas')

                valor_recebido = float(valor_recebido)

                if valor_recebido < total:
                    flash("Valor recebido menor que o total da venda")
                    return redirect('/vendas')

                troco = valor_recebido - total

            else:
                valor_recebido = None

        else:
            # fiado
            forma_pagamento = None
            valor_recebido = None

        # registrar venda
        cursor.execute("""
            INSERT INTO vendas (
                produto_id,
                quantidade,
                valor_total,
                data_venda,
                tipo_venda,
                funcionario_nome,
                forma_pagamento,
                valor_recebido,
                troco
            )
            VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?, ?)
        """, (
            produto_id,
            quantidade,
            total,
            tipo_venda,
            funcionario_nome,
            forma_pagamento,
            valor_recebido,
            troco
        ))

        # atualizar estoque
        cursor.execute("""
            UPDATE produtos
            SET estoque = estoque - ?
            WHERE id = ?
        """, (quantidade, produto_id))

        conn.commit()

        if troco is not None:
            flash(
                f"Venda registrada: {quantidade}x {nome} | Troco: R$ {troco:.2f}"
            )
        else:
            flash(
                f"Venda registrada: {quantidade}x {nome}"
            )

        return redirect('/vendas')

    # ---------------- GET ----------------

    cursor.execute("""
        SELECT id, nome, estoque
        FROM produtos
    """)
    produtos = cursor.fetchall()

    cursor.execute("""
        SELECT
            v.id,
            p.nome,
            v.quantidade,
            v.valor_total,
            v.data_venda,
            v.tipo_venda,
            v.funcionario_nome,
            v.forma_pagamento,
            v.troco
        FROM vendas v
        JOIN produtos p
            ON v.produto_id = p.id
        ORDER BY v.data_venda DESC
    """)
    vendas = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0)
        FROM vendas
    """)
    faturamento_total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM vendas
    """)
    total_vendas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(quantidade), 0)
        FROM vendas
    """)
    total_itens = cursor.fetchone()[0]

    cursor.execute("""
        SELECT id, nome
        FROM funcionarios
        ORDER BY nome
    """)
    funcionarios = cursor.fetchall()

    conn.close()

    return render_template(
        "vendas.html",
        produtos=produtos,
        vendas=vendas,
        faturamento_total=faturamento_total,
        total_vendas=total_vendas,
        total_itens=total_itens,
        funcionarios=funcionarios
    )


# ---------------- RELATÓRIO ----------------
@app.route('/relatorio_vendas')
def relatorio_vendas():
    conn = conectar()
    cursor = conn.cursor()

    #  TOTAL DO DIA (VALOR)
    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0)
        FROM vendas
        WHERE date(data_venda) = date('now')
    """)
    vendas_dia_total = cursor.fetchone()[0]

    #  PRODUTOS VENDIDOS NO DIA
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

    #  TOTAL DO MÊS
    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0)
        FROM vendas
        WHERE strftime('%Y-%m', data_venda) = strftime('%Y-%m', 'now')
    """)
    vendas_mes = cursor.fetchone()[0]

    #  TOTAL GERAL
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

@app.route('/fechar_caixa', methods=['GET', 'POST'])
def fechar_caixa():

    conn = conectar()
    cursor = conn.cursor()

    # procura caixa aberto
    cursor.execute("""
        SELECT *
        FROM caixas
        WHERE status = 'ABERTO'
        ORDER BY id DESC
        LIMIT 1
    """)

    caixa = cursor.fetchone()

    if not caixa:
        flash("Nenhum caixa aberto.")
        conn.close()
        return redirect('/')

    # ---------------- POST (FECHAR CAIXA) ----------------
    if request.method == 'POST':

        cursor.execute("""
            SELECT COALESCE(SUM(valor_total), 0)
            FROM vendas
            WHERE date(data_venda) = date('now')
        """)

        total_dia = cursor.fetchone()[0]

        cursor.execute("""
            UPDATE caixas
            SET
                data_fechamento = datetime('now'),
                valor_vendido = ?,
                status = 'FECHADO'
            WHERE id = ?
        """, (total_dia, caixa[0]))

        conn.commit()
        conn.close()

        flash(f"Caixa fechado com sucesso. Total vendido: R$ {total_dia:.2f}")
        return redirect('/')

    # ---------------- GET (RESUMO) ----------------

    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0)
        FROM vendas
        WHERE date(data_venda) = date('now')
    """)
    total_caixa = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(quantidade), 0)
        FROM vendas
        WHERE date(data_venda) = date('now')
    """)
    itens_dia = cursor.fetchone()[0]

    cursor.execute("""
        SELECT produtos.nome, SUM(vendas.quantidade) as total_qtd
        FROM vendas
        JOIN produtos ON vendas.produto_id = produtos.id
        WHERE date(vendas.data_venda) = date('now')
        GROUP BY produtos.nome
        ORDER BY total_qtd DESC
        LIMIT 5
    """)
    ranking = cursor.fetchall()

    conn.close()

    return render_template(
        "fechar_caixa.html",
        total_caixa=total_caixa,
        itens_dia=itens_dia,
        ranking=ranking,
        caixa=caixa
    )

@app.route('/fiado_funcionario/<nome>')
def fiado_funcionario(nome):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            produtos.nome,
            vendas.quantidade,
            vendas.valor_total,
            vendas.data_venda
        FROM vendas
        JOIN produtos ON vendas.produto_id = produtos.id
        WHERE vendas.tipo_venda = 'FIADO'
        AND vendas.funcionario_nome = ?
        ORDER BY vendas.data_venda DESC
    """, (nome,))

    compras = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0)
        FROM vendas
        WHERE tipo_venda = 'FIADO'
        AND funcionario_nome = ?
    """, (nome,))

    total = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "fiado_funcionario.html",
        nome=nome,
        compras=compras,
        total=total
    )

@app.route('/funcionarios', methods=['GET', 'POST'])
def funcionarios():
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']

        cursor.execute("""
            INSERT INTO funcionarios (nome)
            VALUES (?)
        """, (nome,))

        conn.commit()
        flash("Funcionário cadastrado com sucesso!")
        return redirect('/funcionarios')

    cursor.execute("SELECT * FROM funcionarios")
    lista = cursor.fetchall()

    conn.close()

    return render_template("funcionarios.html", funcionarios=lista)

@app.route('/abrir_caixa', methods=['GET', 'POST'])
def abrir_caixa():

    conn = conectar()
    cursor = conn.cursor()

    # verifica caixa aberto
    cursor.execute("""
        SELECT id
        FROM caixas
        WHERE status = 'ABERTO'
        LIMIT 1
    """)

    caixa_existente = cursor.fetchone()

    if caixa_existente:
        flash("Já existe um caixa aberto.")
        conn.close()
        return redirect('/')

    if request.method == 'POST':

        valor_inicial = float(request.form['valor_inicial'])

        cursor.execute("""
            INSERT INTO caixas (
                data_abertura,
                valor_inicial,
                status
            )
            VALUES (
                datetime('now'),
                ?,
                'ABERTO'
            )
        """, (valor_inicial,))

        conn.commit()
        conn.close()

        flash("Caixa aberto com sucesso!")
        return redirect('/')

    conn.close()

    return render_template(
        'abrir_caixa.html'
    )

if __name__ == '__main__':
    app.run(debug=True)