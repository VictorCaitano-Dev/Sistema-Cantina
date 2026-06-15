from flask import Flask, render_template, request, redirect, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'cantina'

def conectar():
    caminho = os.path.abspath("cantina2.db")
    return sqlite3.connect(caminho)


@app.route('/')
def home():
    conn = conectar()
    cursor = conn.cursor()

    # Total de produtos
    cursor.execute("SELECT COUNT(*) FROM produtos")
    total_produtos = cursor.fetchone()[0]

    # Total de vendas
    cursor.execute("SELECT COUNT(*) FROM vendas")
    total_vendas = cursor.fetchone()[0]

    # Faturamento total
    cursor.execute("SELECT SUM(valor_total) FROM vendas")
    faturamento = cursor.fetchone()[0]

    if faturamento is None:
        faturamento = 0

    conn.close()

    return render_template(
        'index.html',
        total_produtos=total_produtos,
        total_vendas=total_vendas,
        faturamento=faturamento
    )


@app.route('/produtos', methods=['GET', 'POST'])
def produtos():
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        estoque = int(request.form['estoque'])

        cursor.execute("""
            INSERT INTO produtos (nome, preco, estoque)
            VALUES (?, ?, ?)
        """, (nome, preco, estoque))

        conn.commit()
        conn.close()

        flash("Produto cadastrado com sucesso!")
        return redirect('/produtos')

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

    conn.close()

    return render_template('produtos.html', produtos=produtos)


@app.route('/vendas', methods=['GET', 'POST'])
def vendas():
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        produto_id = int(request.form['produto_id'])
        quantidade = int(request.form['quantidade'])

        cursor.execute("""
            SELECT nome, preco, estoque
            FROM produtos
            WHERE id = ?
        """, (produto_id,))

        produto = cursor.fetchone()

        if produto is None:
            flash("Produto não encontrado.")
        else:
            nome, preco, estoque = produto

            if quantidade <= 0:
                flash("A quantidade precisa ser maior que zero.")
            elif quantidade > estoque:
                flash(f"Estoque insuficiente. Estoque atual de {nome}: {estoque}")
            else:
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
                flash(f"Venda registrada com sucesso! Total: R$ {valor_total:.2f}")

        conn.close()
        return redirect('/vendas')

    cursor.execute("SELECT * FROM produtos")
    produtos = cursor.fetchall()

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

    conn.close()

    return render_template('vendas.html', produtos=produtos, vendas=vendas)


@app.route('/excluir_produto/<int:id>')
def excluir_produto(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM vendas
        WHERE produto_id = ?
    """, (id,))

    total_vendas = cursor.fetchone()[0]

    if total_vendas > 0:
        flash("Não é possível excluir este produto porque ele já possui vendas registradas.")
        conn.close()
        return redirect('/produtos')

    cursor.execute("""
        DELETE FROM produtos
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    flash("Produto excluído com sucesso!")
    return redirect('/produtos')


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
        SELECT id, nome, preco, estoque
        FROM produtos
        WHERE id = ?
    """, (id,))

    produto = cursor.fetchone()
    conn.close()

    return render_template('editar_produto.html', produto=produto)


if __name__ == '__main__':
    app.run(debug=True)