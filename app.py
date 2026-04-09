import sqlite3
import sys
import string

# ==========================================
# CONFIGURAÇÕES DE BANCO DE DADOS
# ==========================================
def conectar():
    return sqlite3.connect("magicpark_cli.db")

def inicializar_banco():
    conn = conectar()
    cursor = conn.cursor()
    
    # Criação das tabelas
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario TEXT UNIQUE, senha TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, telefone TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, preco REAL)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_nome TEXT, produto_nome TEXT, qtde INTEGER, total REAL)''')
    
    # Criar usuário admin padrão se não existir
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha) VALUES ('admin', '1234')")
    
    conn.commit()
    conn.close()

# ==========================================
# MÓDULOS DO SISTEMA
# ==========================================

def tela_login():
    print("=" * 40)
    print(" 🎟️  BEM-VINDO AO MAGICPARK TERMINAL 🎟️ ")
    print("=" * 40)
    
    tentativas = 3
    while tentativas > 0:
        usuario = input("Usuário: ").strip()
        senha = input("Senha: ").strip()
        
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND senha=?", (usuario, senha))
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            print("\n✅ Login efetuado com sucesso!")
            menu_principal()
            break
        else:
            tentativas -= 1
            print(f"❌ Usuário ou senha incorretos. Tentativas restantes: {tentativas}\n")
    
    if tentativas == 0:
        print("🔒 Acesso bloqueado. Encerrando o sistema...")
        sys.exit()

def cadastrar_cliente():
    print("\n--- 👥 CADASTRO DE VISITANTE ---")
    nome_bruto = input("Nome do Visitante: ").strip()
    telefone = input("Telefone: ").strip()
    
    if nome_bruto and telefone:
        # Usando a biblioteca string para formatar o nome (Ex: "joao da silva" -> "Joao Da Silva")
        nome_formatado = string.capwords(nome_bruto)
        
        conn = conectar()
        conn.execute("INSERT INTO clientes (nome, telefone) VALUES (?, ?)", (nome_formatado, telefone))
        conn.commit()
        conn.close()
        print(f"✅ Visitante '{nome_formatado}' cadastrado com sucesso!")
    else:
        print("❌ Erro: Todos os campos são obrigatórios.")

def cadastrar_produto():
    print("\n--- 🍿 CADASTRO DE PRODUTO/INGRESSO ---")
    nome_bruto = input("Nome do Produto (Ex: Passaporte VIP): ").strip()
    preco_str = input("Preço (R$): ").replace(",", ".").strip()
    
    if nome_bruto and preco_str:
        nome_formatado = string.capwords(nome_bruto)
        try:
            preco = float(preco_str)
            conn = conectar()
            conn.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome_formatado, preco))
            conn.commit()
            conn.close()
            print(f"✅ Produto '{nome_formatado}' cadastrado com sucesso (R$ {preco:.2f})!")
        except ValueError:
            print("❌ Erro: Digite um valor numérico válido para o preço.")
    else:
        print("❌ Erro: Todos os campos são obrigatórios.")

def realizar_venda():
    print("\n--- 🎟️  NOVA VENDA ---")
    conn = conectar()
    cursor = conn.cursor()
    
    # Listar Clientes
    cursor.execute("SELECT id, nome FROM clientes")
    clientes = cursor.fetchall()
    if not clientes:
        print("❌ Nenhum cliente cadastrado. Cadastre um cliente primeiro.")
        conn.close()
        return

    print("\n-- Clientes Disponíveis --")
    for cli in clientes:
        print(f"[{cli[0]}] {cli[1]}")
    
    try:
        id_cli = int(input("Digite o ID do cliente: "))
        cliente_selecionado = next((c for c in clientes if c[0] == id_cli), None)
        if not cliente_selecionado:
            print("❌ Cliente não encontrado.")
            return
    except ValueError:
        print("❌ ID inválido.")
        return

    # Listar Produtos
    cursor.execute("SELECT id, nome, preco FROM produtos")
    produtos = cursor.fetchall()
    if not produtos:
        print("❌ Nenhum produto cadastrado. Cadastre um produto primeiro.")
        conn.close()
        return

    print("\n-- Produtos Disponíveis --")
    for prod in produtos:
        print(f"[{prod[0]}] {prod[1]} - R$ {prod[2]:.2f}")
    
    try:
        id_prod = int(input("Digite o ID do produto: "))
        produto_selecionado = next((p for p in produtos if p[0] == id_prod), None)
        if not produto_selecionado:
            print("❌ Produto não encontrado.")
            return
            
        qtde = int(input("Quantidade: "))
        if qtde <= 0:
            print("❌ A quantidade deve ser maior que zero.")
            return
            
    except ValueError:
        print("❌ Entrada inválida. Digite apenas números.")
        return

    # Salvar Venda
    nome_cli = cliente_selecionado[1]
    nome_prod = produto_selecionado[1]
    preco_unit = produto_selecionado[2]
    total = qtde * preco_unit

    conn.execute("INSERT INTO vendas (cliente_nome, produto_nome, qtde, total) VALUES (?, ?, ?, ?)", 
                 (nome_cli, nome_prod, qtde, total))
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 30)
    print(f"🎡 VENDA CONCLUÍDA COM SUCESSO! 🎡")
    print(f"Cliente: {nome_cli}")
    print(f"Produto: {qtde}x {nome_prod}")
    print(f"Total a Pagar: R$ {total:.2f}")
    print("=" * 30)

def menu_principal():
    while True:
        print("\n" + "=" * 40)
        print(" 🎪 MENU PRINCIPAL - MAGICPARK 🎪 ")
        print("=" * 40)
        print("1. Cadastrar Novo Visitante (Cliente)")
        print("2. Cadastrar Novo Ingresso/Produto")
        print("3. Realizar Venda")
        print("4. Sair do Sistema")
        
        opcao = input("\nEscolha uma opção (1-4): ").strip()
        
        if opcao == '1':
            cadastrar_cliente()
        elif opcao == '2':
            cadastrar_produto()
        elif opcao == '3':
            realizar_venda()
        elif opcao == '4':
            print("\nEncerrando o MagicPark SisVenda. Volte sempre! 🎢")
            sys.exit()
        else:
            print("❌ Opção inválida. Tente novamente.")

# ==========================================
# EXECUÇÃO DO SCRIPT
# ==========================================
if __name__ == "__main__":
    inicializar_banco()
    tela_login()