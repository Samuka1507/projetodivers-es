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
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario TEXT UNIQUE, senha TEXT)''')
    
    # Atualizado com dois saldos
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, cpf TEXT UNIQUE, senha TEXT,
                        saldo_15 INTEGER DEFAULT 0,
                        saldo_20 INTEGER DEFAULT 0)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, preco REAL)''')
    
    # Atualizado com o preço do brinquedo
    cursor.execute('''CREATE TABLE IF NOT EXISTS brinquedos (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT, capacidade_total INTEGER, vagas_disponiveis INTEGER,
                        preco INTEGER)''')
                        
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_nome TEXT, produto_nome TEXT, qtde INTEGER, total REAL)''')
                        
    # Atualizado com o preço gasto para devolver o ingresso certo em caso de cancelamento
    cursor.execute('''CREATE TABLE IF NOT EXISTS reservas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cliente_nome TEXT, brinquedo_nome TEXT, preco_gasto INTEGER)''')
    
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
    
    cpf = input("Digite seu CPF (apenas números): ").strip()
    if not cpf: return

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nome, senha FROM clientes WHERE cpf=?", (cpf,))
    resultado = cursor.fetchone()
    
    if resultado:
        nome_cliente, senha_cadastrada = resultado
        senha_digitada = input("Digite sua senha: ").strip()
        if senha_digitada == senha_cadastrada:
            conn.close()
            menu_visitante(nome_cliente, cpf)
        else:
            print("❌ Senha incorreta!")
            conn.close()
    else:
        print("\n👋 Novo por aqui? Vamos te cadastrar!")
        nome_bruto = input("Nome completo: ").strip()
        senha_nova = input("Crie uma senha: ").strip()
        
        if nome_bruto and senha_nova:
            nome_cliente = string.capwords(nome_bruto)
            cursor.execute("INSERT INTO clientes (nome, cpf, senha, saldo_15, saldo_20) VALUES (?, ?, ?, 0, 0)", 
                           (nome_cliente, cpf, senha_nova))
            conn.commit()
            print(f"✅ Bem-vindo, {nome_cliente}!")
            conn.close()
            menu_visitante(nome_cliente, cpf)
        else:
            print("❌ Dados inválidos.")
            conn.close()

def ver_perfil_e_ingressos(nome_cliente, cpf):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT saldo_15, saldo_20 FROM clientes WHERE cpf=?", (cpf,))
    s15, s20 = cursor.fetchone()
    
    print("\n" + "─" * 30)
    print(f"👤 PERFIL: {nome_cliente}")
    print(f"🎟️  INGRESSOS R$ 15: {s15} disponíveis")
    print(f"🎟️  INGRESSOS R$ 20: {s20} disponíveis")
    print("─" * 30)
    
    print("\n🎢 SUAS RESERVAS ATUAIS:")
    cursor.execute("SELECT id, brinquedo_nome, preco_gasto FROM reservas WHERE cliente_nome=?", (nome_cliente,))
    reservas = cursor.fetchall()
    
    if not reservas:
        print("   Nenhuma reserva ativa.")
    else:
        for res in reservas:
            print(f"   ID: {res[0]} | Brinquedo: {res[1]} (Categoria R$ {res[2]})")
    print("─" * 30)
    conn.close()
    return reservas

def comprar_produto(nome_cliente, cpf):
    print("\n--- 🍔 LOJA E BILHETERIA 🍿 ---")
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, preco FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    
    if not produtos:
        print("❌ A loja está vazia no momento.")
        return

    carrinho = []
    total_compra = 0.0
    ingressos_15 = 0
    ingressos_20 = 0

    while True:
        print("\n-- Cardápio / Lojinha --")
        for prod in produtos:
            print(f"[{prod[0]}] {prod[1]} - R$ {prod[2]:.2f}")
        print("\n[0] FINALIZAR COMPRA E PAGAR")
        print("[C] CANCELAR TUDO")
        
        escolha = input("\nDigite o número do item (ou 0 para pagar): ").strip().upper()
        
        if escolha == '0': break
        elif escolha == 'C':
            print("🛒 Compra cancelada.")
            return

        try:
            id_prod = int(escolha)
            item = next((p for p in produtos if p[0] == id_prod), None)
            
            if item:
                qtde = int(input(f"Quantas unidades de '{item[1]}'? "))
                if qtde > 0:
                    subtotal = qtde * item[2]
                    carrinho.append({'nome': item[1], 'qtde': qtde, 'subtotal': subtotal})
                    total_compra += subtotal
                    
                    # Detectar tipo de ingresso comprado
                    if "ingresso" in item[1].lower() or "passaporte" in item[1].lower():
                        if item[2] == 15.0: ingressos_15 += qtde
                        elif item[2] == 20.0: ingressos_20 += qtde
                        
                    print(f"✅ Adicionado! Valor do carrinho: R$ {total_compra:.2f}")
                else:
                    print("❌ Quantidade inválida.")
            else:
                print("❌ Item não encontrado.")
        except ValueError:
            print("❌ Entrada inválida.")

    if carrinho:
        print("\n" + "💳" * 15)
        print(" RESUMO DA SUA COMPRA ")
        print("💳" * 15)
        for c in carrinho: print(f"{c['qtde']}x {c['nome']} ........... R$ {c['subtotal']:>6.2f}")
        print("-" * 30)
        print(f"TOTAL A PAGAR:      R$ {total_compra:>6.2f}")
        
        confirmar = input("\nConfirmar pagamento? (S/N): ").strip().upper()
        if confirmar == 'S':
            conn = conectar()
            cursor = conn.cursor()
            
            for c in carrinho:
                cursor.execute("INSERT INTO vendas (cliente_nome, produto_nome, qtde, total) VALUES (?, ?, ?, ?)", 
                             (nome_cliente, c['nome'], c['qtde'], c['subtotal']))
            
            if ingressos_15 > 0: cursor.execute("UPDATE clientes SET saldo_15 = saldo_15 + ? WHERE cpf = ?", (ingressos_15, cpf))
            if ingressos_20 > 0: cursor.execute("UPDATE clientes SET saldo_20 = saldo_20 + ? WHERE cpf = ?", (ingressos_20, cpf))
                
            conn.commit()
            conn.close()
            print("\n✅ Pagamento aprovado!")
            if ingressos_15 > 0: print(f"🎟️  +{ingressos_15} ingresso(s) de R$ 15 adicionado(s)!")
            if ingressos_20 > 0: print(f"🎟️  +{ingressos_20} ingresso(s) de R$ 20 adicionado(s)!")
        else:
            print("❌ Pagamento cancelado.")

def reservar_brinquedo(nome_cliente, cpf):
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("SELECT saldo_15, saldo_20 FROM clientes WHERE cpf=?", (cpf,))
    s15, s20 = cursor.fetchone()
    
    cursor.execute("SELECT id, nome, vagas_disponiveis, preco FROM brinquedos WHERE vagas_disponiveis > 0")
    brinquedos = cursor.fetchall()
    
    if not brinquedos:
        print("❌ Nenhum brinquedo disponível.")
        conn.close()
        return

    print(f"\n--- 🎢 BRINQUEDOS DE R$ 15 (Seu saldo: {s15} ingressos) ---")
    tem_15 = False
    for b in brinquedos:
        if b[3] == 15:
            print(f"[{b[0]}] {b[1]} (Vagas: {b[2]})")
            tem_15 = True
    if not tem_15: print("   Nenhum brinquedo de R$ 15 disponível no momento.")

    print(f"\n--- 🎡 BRINQUEDOS DE R$ 20 (Seu saldo: {s20} ingressos) ---")
    tem_20 = False
    for b in brinquedos:
        if b[3] == 20:
            print(f"[{b[0]}] {b[1]} (Vagas: {b[2]})")
            tem_20 = True
    if not tem_20: print("   Nenhum brinquedo de R$ 20 disponível no momento.")
        
    try:
        id_brinq = int(input("\nEscolha o ID do brinquedo (ou 0 para sair): "))
        if id_brinq == 0: return
        
        b_sel = next((b for b in brinquedos if b[0] == id_brinq), None)
        
        if b_sel:
            preco_brinq = b_sel[3]
            
            # Validação de saldo
            if preco_brinq == 15 and s15 <= 0:
                print("❌ Você não tem ingressos de R$ 15. Compre na bilheteria.")
            elif preco_brinq == 20 and s20 <= 0:
                print("❌ Você não tem ingressos de R$ 20. Compre na bilheteria.")
            else:
                # Efetivar a reserva
                cursor.execute("INSERT INTO reservas (cliente_nome, brinquedo_nome, preco_gasto) VALUES (?, ?, ?)", 
                               (nome_cliente, b_sel[1], preco_brinq))
                cursor.execute("UPDATE brinquedos SET vagas_disponiveis = vagas_disponiveis - 1 WHERE id = ?", (id_brinq,))
                
                if preco_brinq == 15:
                    cursor.execute("UPDATE clientes SET saldo_15 = saldo_15 - 1 WHERE cpf = ?", (cpf,))
                else:
                    cursor.execute("UPDATE clientes SET saldo_20 = saldo_20 - 1 WHERE cpf = ?", (cpf,))
                
                conn.commit()
                print(f"🎟️  Reserva confirmada em: {b_sel[1]} (Gasto 1 ingresso de R$ {preco_brinq})!")
        else:
            print("❌ Brinquedo não encontrado.")
    except ValueError:
        print("❌ Entrada inválida.")
    finally:
        conn.close()

def cancelar_reserva(nome_cliente, cpf):
    print("\n--- ↩️  CANCELAR AGENDAMENTO ---")
    reservas = ver_perfil_e_ingressos(nome_cliente, cpf)
    
    if not reservas: return

    try:
        id_res = int(input("\nDigite o ID da reserva que deseja CANCELAR (ou 0 para voltar): "))
        if id_res == 0: return
        
        res_sel = next((r for r in reservas if r[0] == id_res), None)
        
        if res_sel:
            preco_gasto = res_sel[2]
            conn = conectar()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE brinquedos SET vagas_disponiveis = vagas_disponiveis + 1 WHERE nome = ?", (res_sel[1],))
            
            if preco_gasto == 15:
                cursor.execute("UPDATE clientes SET saldo_15 = saldo_15 + 1 WHERE cpf = ?", (cpf,))
            elif preco_gasto == 20:
                cursor.execute("UPDATE clientes SET saldo_20 = saldo_20 + 1 WHERE cpf = ?", (cpf,))
                
            cursor.execute("DELETE FROM reservas WHERE id = ?", (id_res,))
            
            conn.commit()
            conn.close()
            print(f"✅ Reserva cancelada! Vaga devolvida e ingresso de R$ {preco_gasto} estornado para seu perfil.")
        else:
            print("❌ ID de reserva não encontrado.")
    except ValueError:
        print("❌ Digite um número válido.")

def menu_visitante(nome_cliente, cpf):
    while True:
        print("\n" + "=" * 40)
        print(f" 🎡 MAGICPARK - OLÁ, {nome_cliente.upper()} 🎡 ")
        print("=" * 40)
        print("1. Ver meu Saldo e Reservas")
        print("2. Comprar Ingressos / Comidas (🛒)")
        print("3. Reservar Brinquedo")
        print("4. Cancelar Reserva")
        print("5. Sair")
        
        op = input("\nOpção: ").strip()
        if op == '1': ver_perfil_e_ingressos(nome_cliente, cpf)
        elif op == '2': comprar_produto(nome_cliente, cpf)
        elif op == '3': reservar_brinquedo(nome_cliente, cpf)
        elif op == '4': cancelar_reserva(nome_cliente, cpf)
        elif op == '5': break

# ==========================================
# MÓDULO: ADMINISTRAÇÃO (LOGIN: admin / 1234)
# ==========================================
def menu_admin():
    while True:
        print("\n--- 👔 GERÊNCIA ---")
        print("1. Cadastrar Produto/Ingresso (Dica: Preço deve ser 15.0 ou 20.0 para ingressos)")
        print("2. Cadastrar Brinquedo")
        print("3. Relatório Geral")
        print("4. Voltar")
        op = input("Opção: ").strip()
        if op == '1':
            n = input("Nome do produto (Ex: Ingresso Normal): "); p = float(input("Preço: ").replace(",","."))
            c = conectar(); c.execute("INSERT INTO produtos (nome, preco) VALUES (?,?)", (n,p)); c.commit(); c.close()
            print("✅ Produto salvo!")
        elif op == '2':
            n = input("Nome do brinquedo: "); v = int(input("Capacidade: "))
            while True:
                try:
                    p = int(input("Preço da Categoria do Brinquedo (15 ou 20): "))
                    if p in [15, 20]: break
                    print("❌ Digite apenas 15 ou 20.")
                except ValueError: print("❌ Apenas números.")
            c = conectar(); c.execute("INSERT INTO brinquedos (nome, capacidade_total, vagas_disponiveis, preco) VALUES (?,?,?,?)", (n,v,v,p)); c.commit(); c.close()
            print("✅ Brinquedo salvo!")
        elif op == '3':
            c = conectar(); cur = c.cursor()
            print("\nVAGAS:"); cur.execute("SELECT nome, vagas_disponiveis, capacidade_total, preco FROM brinquedos")
            for r in cur.fetchall(): print(f" - {r[0]} (Cat. R${r[3]}): {r[1]}/{r[2]} vagas")
            cur.execute("SELECT SUM(total) FROM vendas"); print(f"\nCAIXA: R$ {cur.fetchone()[0] or 0:.2f}")
            c.close()
        elif op == '4': break

def tela_login_admin():
    u = input("Usuário: "); s = input("Senha: ")
    if u == 'admin' and s == '1234': menu_admin()
    else: print("❌ Erro de acesso!")

# ==========================================
# INÍCIO
# ==========================================
if __name__ == "__main__":
    inicializar_banco()
    while True:
        print("\n" + "★" * 40 + "\n 🎪 MAGICPARK SYSTEM 🎪 \n" + "★" * 40)
        print("1. Sou Visitante | 2. Administração | 3. Sair")
        e = input("\nEscolha: ").strip()
        if e == '1': acesso_visitante()
        elif e == '2': tela_login_admin()
        elif e == '3': sys.exit()