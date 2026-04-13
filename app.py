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
    
    # Tabela de Usuários Administrativos
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario TEXT UNIQUE, senha TEXT)''')
    
    # Tabela de Clientes ATUALIZADA (Nome, CPF e Senha)
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, cpf TEXT UNIQUE, senha TEXT)''')
    
    # Tabela de Produtos (Comidas, Bebidas, Ingressos)
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, preco REAL)''')
    
    # Tabela de Brinquedos (Controle de Vagas)
    cursor.execute('''CREATE TABLE IF NOT EXISTS brinquedos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, capacidade_total INTEGER, vagas_disponiveis INTEGER)''')
                        
    # Tabelas de Movimentação (Compras e Agendamentos)
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_nome TEXT, produto_nome TEXT, qtde INTEGER, total REAL)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS reservas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_nome TEXT, brinquedo_nome TEXT)''')
    
    # Criar usuário admin padrão se não existir
    cursor.execute("INSERT OR IGNORE INTO usuarios (usuario, senha) VALUES ('admin', '1234')")
    
    conn.commit()
    conn.close()

# ==========================================
# MÓDULO: ÁREA DO VISITANTE (AUTOATENDIMENTO)
# ==========================================
def acesso_visitante():
    print("\n" + "=" * 40)
    print(" 📱 AUTOATENDIMENTO DO VISITANTE 📱 ")
    print("=" * 40)
    
    cpf = input("Digite seu CPF (apenas números) para acessar: ").strip()
    
    if not cpf:
        print("❌ O CPF é obrigatório para acessar.")
        return

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, senha FROM clientes WHERE cpf=?", (cpf,))
    resultado = cursor.fetchone()
    
    # Lógica de Login ou Cadastro
    if resultado:
        nome_cliente = resultado[0]
        senha_cadastrada = resultado[1]
        
        senha_digitada = input("Digite sua senha: ").strip()
        if senha_digitada == senha_cadastrada:
            print(f"\n✅ Que bom te ver de volta, {nome_cliente}!")
            conn.close()
            menu_visitante(nome_cliente)
        else:
            print("❌ Senha incorreta! Acesso negado.")
            conn.close()
    else:
        print("\n👋 Parece que é sua primeira vez aqui! Vamos fazer seu cadastro.")
        nome_bruto = input("Qual o seu nome completo? ").strip()
        senha_nova = input("Crie uma senha de acesso: ").strip()
        
        if not nome_bruto or not senha_nova:
            print("❌ Nome e senha são obrigatórios. Operação cancelada.")
            conn.close()
            return
            
        nome_cliente = string.capwords(nome_bruto)
        try:
            cursor.execute("INSERT INTO clientes (nome, cpf, senha) VALUES (?, ?, ?)", (nome_cliente, cpf, senha_nova))
            conn.commit()
            print(f"\n✅ Cadastro realizado com sucesso! Seja bem-vindo(a), {nome_cliente}!")
            conn.close()
            menu_visitante(nome_cliente)
        except sqlite3.IntegrityError:
            print("❌ Erro ao cadastrar. Verifique se os dados estão corretos.")
            conn.close()

def comprar_produto(nome_cliente):
    print("\n--- 🍔 COMPRAR COMIDA / PRODUTOS 🍿 ---")
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, nome, preco FROM produtos")
    produtos = cursor.fetchall()
    
    if not produtos:
        print("❌ Nenhuma opção disponível no momento. Fale com a gerência.")
        conn.close()
        return

    print("\n-- Cardápio / Lojinha --")
    for prod in produtos:
        print(f"[{prod[0]}] {prod[1]} - R$ {prod[2]:.2f}")
    
    try:
        id_prod = int(input("\nDigite o número do item que deseja: "))
        produto_selecionado = next((p for p in produtos if p[0] == id_prod), None)
        
        if not produto_selecionado:
            print("❌ Item não encontrado.")
            return
            
        qtde = int(input("Quantidade: "))
        if qtde <= 0:
            print("❌ A quantidade deve ser maior que zero.")
            return
            
        nome_prod = produto_selecionado[1]
        preco_unit = produto_selecionado[2]
        total = qtde * preco_unit

        conn.execute("INSERT INTO vendas (cliente_nome, produto_nome, qtde, total) VALUES (?, ?, ?, ?)", 
                     (nome_cliente, nome_prod, qtde, total))
        conn.commit()
        
        print("\n" + "-" * 30)
        print("💳 COMPRA APROVADA!")
        print(f"Item: {qtde}x {nome_prod}")
        print(f"Total pago: R$ {total:.2f}")
        print("-" * 30)
        
    except ValueError:
        print("❌ Entrada inválida. Digite apenas números.")
    finally:
        conn.close()

def reservar_brinquedo(nome_cliente):
    print("\n--- 🎢 AGENDAR BRINQUEDO ---")
    conn = conectar()
    cursor = conn.cursor()
    
    # Mostra apenas brinquedos com vagas > 0
    cursor.execute("SELECT id, nome, vagas_disponiveis, capacidade_total FROM brinquedos WHERE vagas_disponiveis > 0")
    brinquedos = cursor.fetchall()
    
    if not brinquedos:
        print("❌ Poxa! Todos os brinquedos estão lotados no momento ou não foram cadastrados.")
        conn.close()
        return

    print("\n-- Brinquedos com Vagas Abertas --")
    for b in brinquedos:
        print(f"[{b[0]}] {b[1]} - Vagas Livres: {b[2]}/{b[3]}")
        
    try:
        id_brinq = int(input("\nDigite o número do brinquedo que deseja ir: "))
        brinquedo_selecionado = next((b for b in brinquedos if b[0] == id_brinq), None)
        
        if not brinquedo_selecionado:
            print("❌ Brinquedo não encontrado ou lotado.")
            return
            
        nome_brinquedo = brinquedo_selecionado[1]
        vagas_atuais = brinquedo_selecionado[2]
        
        # Registra a reserva e diminui 1 vaga
        cursor.execute("INSERT INTO reservas (cliente_nome, brinquedo_nome) VALUES (?, ?)", (nome_cliente, nome_brinquedo))
        cursor.execute("UPDATE brinquedos SET vagas_disponiveis = ? WHERE id = ?", (vagas_atuais - 1, id_brinq))
        conn.commit()
        
        print("\n" + "-" * 30)
        print("🎟️  AGENDAMENTO CONFIRMADO!")
        print(f"Você garantiu seu lugar no(a) {nome_brinquedo}.")
        print("Vá até a fila no horário combinado!")
        print("-" * 30)

    except ValueError:
        print("❌ Entrada inválida. Digite apenas os números correspondentes.")
    finally:
        conn.close()

def menu_visitante(nome_cliente):
    while True:
        print("\n" + "=" * 40)
        print(f" 🎡 PAINEL DO VISITANTE: {nome_cliente.upper()} 🎡 ")
        print("=" * 40)
        print("1. Comprar Comida ou Produtos")
        print("2. Agendar Fila nos Brinquedos")
        print("3. Sair / Deslogar")
        
        opcao = input("\nO que você deseja fazer? (1-3): ").strip()
        
        if opcao == '1':
            comprar_produto(nome_cliente)
        elif opcao == '2':
            reservar_brinquedo(nome_cliente)
        elif opcao == '3':
            print(f"\nAté logo, {nome_cliente}! Aproveite o parque!")
            break
        else:
            print("❌ Opção inválida.")

# ==========================================
# MÓDULO: ÁREA DA GERÊNCIA (ADMIN)
# ==========================================
def tela_login_admin():
    print("\n--- 🔒 ACESSO RESTRITO (ADMINISTRAÇÃO) ---")
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
            print("\n✅ Acesso Autorizado!")
            menu_admin()
            break
        else:
            tentativas -= 1
            print(f"❌ Credenciais incorretas. Tentativas: {tentativas}\n")
    
    if tentativas == 0:
        print("🔒 Acesso bloqueado. Retornando ao menu principal...")

def cadastrar_produto():
    print("\n--- 📦 CADASTRAR NOVO PRODUTO NO CARDÁPIO ---")
    nome_bruto = input("Nome (Ex: Pipoca Doce): ").strip()
    preco_str = input("Preço (R$): ").replace(",", ".").strip()
    
    if nome_bruto and preco_str:
        nome_formatado = string.capwords(nome_bruto)
        try:
            preco = float(preco_str)
            conn = conectar()
            conn.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)", (nome_formatado, preco))
            conn.commit()
            conn.close()
            print(f"✅ Produto '{nome_formatado}' adicionado ao sistema (R$ {preco:.2f})!")
        except ValueError:
            print("❌ Erro: Digite um valor numérico válido.")
    else:
        print("❌ Erro: Todos os campos são obrigatórios.")

def cadastrar_brinquedo():
    print("\n--- 🎢 CADASTRAR NOVO BRINQUEDO ---")
    nome_bruto = input("Nome do Brinquedo (Ex: Roda Gigante): ").strip()
    
    if nome_bruto:
        nome_formatado = string.capwords(nome_bruto)
        try:
            capacidade = int(input("Total de Vagas da Rodada: "))
            if capacidade <= 0:
                print("❌ A capacidade deve ser maior que zero.")
                return
                
            conn = conectar()
            conn.execute("INSERT INTO brinquedos (nome, capacidade_total, vagas_disponiveis) VALUES (?, ?, ?)", 
                         (nome_formatado, capacidade, capacidade))
            conn.commit()
            conn.close()
            print(f"✅ Brinquedo '{nome_formatado}' ativado com {capacidade} vagas!")
        except ValueError:
            print("❌ Erro: Digite um número inteiro.")
    else:
        print("❌ Erro: O nome é obrigatório.")

def ver_relatorios():
    print("\n--- 📊 RELATÓRIOS DO PARQUE ---")
    conn = conectar()
    cursor = conn.cursor()
    
    print("\n>> STATUS DOS BRINQUEDOS:")
    cursor.execute("SELECT nome, vagas_disponiveis, capacidade_total FROM brinquedos")
    brinqs = cursor.fetchall()
    if not brinqs:
        print("   Nenhum brinquedo cadastrado.")
    for b in brinqs:
        print(f"   {b[0]} -> Vagas: {b[1]}/{b[2]}")

    print("\n>> TOTAL ARRECADADO EM VENDAS:")
    cursor.execute("SELECT SUM(total) FROM vendas")
    total_vendas = cursor.fetchone()[0]
    total_vendas = total_vendas if total_vendas else 0.0
    print(f"   Caixa Total: R$ {total_vendas:.2f}")
    
    conn.close()
    input("\nPressione ENTER para voltar...")

def menu_admin():
    while True:
        print("\n" + "=" * 40)
        print(" 👔 PAINEL DA GERÊNCIA 👔 ")
        print("=" * 40)
        print("1. Adicionar Produto / Comida")
        print("2. Adicionar Brinquedo")
        print("3. Ver Relatórios e Status das Vagas")
        print("4. Voltar à Tela Inicial")
        
        opcao = input("\nEscolha uma opção (1-4): ").strip()
        
        if opcao == '1':
            cadastrar_produto()
        elif opcao == '2':
            cadastrar_brinquedo()
        elif opcao == '3':
            ver_relatorios()
        elif opcao == '4':
            break
        else:
            print("❌ Opção inválida.")

# ==========================================
# EXECUÇÃO DO SCRIPT (TELA INICIAL)
# ==========================================
if __name__ == "__main__":
    inicializar_banco()
    
    while True:
        print("\n" + "★" * 40)
        print(" 🎪 BEM-VINDO AO MAGICPARK TERMINAL 🎪 ")
        print("★" * 40)
        print("Quem está acessando o sistema?")
        print("1. Sou um Visitante (Login / Cadastro)")
        print("2. Sou da Administração")
        print("3. Encerrar Sistema")
        
        escolha = input("\nDigite a opção (1-3): ").strip()
        
        if escolha == '1':
            acesso_visitante()
        elif escolha == '2':
            tela_login_admin()
        elif escolha == '3':
            print("\nDesligando os totens... Volte sempre! 🎢")
            sys.exit()
        else:
            print("❌ Opção inválida. Escolha 1, 2 ou 3.")