import os
import sqlite3
from crud_vendas import registrar_venda, listar_vendas

def conectar():
    caminho = os.path.abspath("cantina2.db")
    print("BANCO USADO PELO PYTHON:", caminho)
    return sqlite3.connect(caminho)

def cadastrar_produto(): #função de cadastrar o produto
    nome = input("Nome do produto: ") #pede o nome do produto
    preco = float(input("Preço: R$ ")) #pede o preço do produto
    estoque = int(input("Quantidade em estoque: ")) #pede a quantidade em estoque do produto

    conn = conectar() #conecta a função ao banco de dados
    cursor = conn.cursor() #envia comandos ao banco de dados
    print("Banco:", conn)
    import os

    print("Banco utilizado:")
    print(os.path.abspath("cantina.db"))

    cursor.execute(""" 
        INSERT INTO produtos (nome, preco, estoque)
        VALUES (?, ?, ?)
    """, (nome, preco, estoque)) #aqui o cursor envia o comando de insert, que insere produtos no banco de dados.

    conn.commit() #essa linha salva as alterações 
    conn.close() #fecha a conexão com o banco, como se fosse o ponto final. 

    print("Produto cadastrado com sucesso!") #mostra que o produto foi cadastrado 

def listar_produtos(): #função de listar os produtos que já foram cadastrados
    conn = conectar() #conecta a função ao banco de dados
    cursor = conn.cursor() #envia comandos ao banco de dados

    cursor.execute("SELECT * FROM produtos") #o cursor seleciona (SELECT), tudo (*), de (FROM), dos produtos

    produtos = cursor.fetchall() #mostra os produtos em ordem, com seu nome, sabor, preço e estoque.

    print("\n===== PRODUTOS =====\n") #mostra um mini menu interativo

    for produto in produtos: #faz um laço de repetição, pra cada produto na lista de produtos
        print(
            f"ID: {produto[0]} | "
            f"Nome: {produto[1]} | "
            f"Preço: R$ {produto[2]:.2f} | "
            f"Estoque: {produto[3]}"
        ) #aqui é mostrado o produto, com seu id, nome, preço e estoque. 

    conn.close() #finaliza a função.

def atualizar_produto(): #função de atualizar o produto
    id_produto = int(input("Digite o ID do produto: ")) #pede o id do produto
    novo_estoque = int(input("Novo estoque: ")) #pede uma nova quantidade de estoque

    conn = conectar() #conecta a função ao banco de dados
    cursor = conn.cursor() #envia comandos ao banco de dados

    cursor.execute("""
        UPDATE produtos
        SET estoque = ?
        WHERE id = ?
    """, (novo_estoque, id_produto)) #o cursor executa o comando de dar UPDATE no produto, com estoque e id.

    conn.commit() #essa linha salva as alterações
    conn.close()#fecha a conexão com o banco, como se fosse o ponto final.

    print("Estoque atualizado com sucesso!") #mostra que o estoque foi atualizado com sucesso

def excluir_produto(): #função de excluir o produto
    id_produto = int(input("Digite o ID do produto que deseja excluir: ")) #pede o id do produto que deseja excluir 

    conn = conectar() #conecta a função ao banco de dados
    cursor = conn.cursor() #envia comandos ao banco de dados

    cursor.execute("""
        DELETE FROM produtos
        WHERE id = ?
    """, (id_produto,)) #aqui o cursor executa a função DELETE, colocando o id e excluindo o respectivo produto.

    conn.commit() #essa linha salva as alterações
    conn.close() #fecha a conexão com o banco

    print("Produto excluído com sucesso!") #mostra que o produto foi excluído

#menu 

while True:

    print("\n===== SISTEMA DA CANTINA =====") #mostra um mini menu com opções
    print("1 - Cadastrar Produto")
    print("2 - Listar Produtos")
    print("3 - Atualizar Estoque")
    print("4 - Excluir Produto")
    print("5 - Registrar venda")
    print("6 - listar vendas")
    print('7 - sair') 

    opcao = input("Escolha uma opção: ") #escolhe a opção

    if opcao == "1":
        cadastrar_produto()

    elif opcao == "2":
        listar_produtos()

    elif opcao == "3":
        atualizar_produto()

    elif opcao == "4":
        excluir_produto()

    elif opcao == "5":
        registrar_venda()
    
    elif opcao == "6":
        listar_vendas()
    
    elif opcao == '7':
        print('Encerrando sistema...')
        break

    else:
        print("Opção inválida!")