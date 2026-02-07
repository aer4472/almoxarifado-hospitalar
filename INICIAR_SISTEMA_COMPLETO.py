"""
INICIALIZAR BANCO COMPLETO COM SUPER ADMIN
Execute: python INICIAR_SISTEMA_COMPLETO.py
"""

import sys
import os

# Adicionar caminhos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import sqlite3

print("=" * 70)
print("    INICIALIZAÇÃO COMPLETA DO SISTEMA")
print("=" * 70)
print()
print("Este script vai:")
print("  1. Criar o banco de dados")
print("  2. Criar todas as tabelas")
print("  3. Criar almoxarifado padrão")
print("  4. Criar Super Administrador")
print()
input("Pressione ENTER para continuar...")
print()

# Caminho do banco
DB_PATH = 'backend/almoxarifado.db'
os.makedirs('backend', exist_ok=True)

try:
    # Conectar ao banco (cria se não existir)
    print("1. Conectando ao banco de dados...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    print("   ✅ Conectado!")
    
    # Verificar se tabela usuarios existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usuarios'")
    if cursor.fetchone():
        print("\n✅ Banco já inicializado!")
        print("\nPromovendo usuário admin para Super Administrador...")
        
        # Verificar se admin existe
        cursor.execute("SELECT id, nome FROM usuarios WHERE username = 'admin'")
        admin = cursor.fetchone()
        
        if admin:
            # Atualizar para super admin
            cursor.execute("UPDATE usuarios SET nivel_acesso = 'admin_geral' WHERE username = 'admin'")
            conn.commit()
            print("✅ Usuário 'admin' promovido para Super Administrador!")
        else:
            print("\n⚠️  Usuário 'admin' não encontrado!")
            print("Criando novo usuário...")
            
            senha_hash = generate_password_hash('admin123')
            cursor.execute("""
                INSERT INTO usuarios (nome, username, senha, nivel_acesso, ativo)
                VALUES ('Administrador do Sistema', 'admin', ?, 'admin_geral', 1)
            """, (senha_hash,))
            conn.commit()
            print("✅ Super Admin criado: admin / admin123")
    
    else:
        print("\n⚠️  Banco vazio! Criando estrutura...")
        
        # Criar tabela almoxarifados
        print("\n2. Criando tabela almoxarifados...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS almoxarifados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL UNIQUE,
                descricao TEXT,
                endereco VARCHAR(200),
                responsavel VARCHAR(100),
                telefone VARCHAR(20),
                ativo BOOLEAN DEFAULT 1,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Criada!")
        
        # Criar tabela usuarios
        print("\n3. Criando tabela usuarios...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL,
                username VARCHAR(50) NOT NULL UNIQUE,
                senha VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                nivel_acesso VARCHAR(20) NOT NULL,
                ativo BOOLEAN DEFAULT 1,
                almoxarifado_id INTEGER,
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (almoxarifado_id) REFERENCES almoxarifados (id)
            )
        """)
        print("   ✅ Criada!")
        
        # Criar tabela categorias
        print("\n4. Criando tabela categorias...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL UNIQUE,
                descricao TEXT
            )
        """)
        print("   ✅ Criada!")
        
        # Criar tabela setores
        print("\n5. Criando tabela setores...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS setores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(100) NOT NULL UNIQUE,
                descricao TEXT,
                responsavel VARCHAR(100),
                ativo BOOLEAN DEFAULT 1
            )
        """)
        print("   ✅ Criada!")
        
        # Criar tabela itens
        print("\n6. Criando tabela itens...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo_barras VARCHAR(50) UNIQUE,
                nome VARCHAR(200) NOT NULL,
                descricao TEXT,
                marca VARCHAR(100),
                unidade_medida VARCHAR(10),
                quantidade FLOAT DEFAULT 0,
                estoque_minimo FLOAT DEFAULT 0,
                lote VARCHAR(50),
                data_validade DATE,
                categoria_id INTEGER,
                almoxarifado_id INTEGER,
                data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (categoria_id) REFERENCES categorias (id),
                FOREIGN KEY (almoxarifado_id) REFERENCES almoxarifados (id)
            )
        """)
        print("   ✅ Criada!")
        
        # Criar tabela movimentacoes
        print("\n7. Criando tabela movimentacoes...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                tipo VARCHAR(20) NOT NULL,
                quantidade FLOAT NOT NULL,
                usuario_id INTEGER NOT NULL,
                setor_id INTEGER,
                observacao TEXT,
                data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES itens (id),
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
                FOREIGN KEY (setor_id) REFERENCES setores (id)
            )
        """)
        print("   ✅ Criada!")
        
        # Criar tabela configuracoes
        print("\n8. Criando tabela configuracoes...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_hospital VARCHAR(200),
                logo_url VARCHAR(500),
                cor_primaria VARCHAR(7) DEFAULT '#0d6efd',
                cor_secundaria VARCHAR(7) DEFAULT '#6c757d',
                cor_navbar VARCHAR(7) DEFAULT '#212529',
                cor_sucesso VARCHAR(7) DEFAULT '#198754',
                rodape_empresa VARCHAR(200),
                rodape_contato VARCHAR(100),
                rodape_instagram VARCHAR(100)
            )
        """)
        print("   ✅ Criada!")
        
        # Inserir configuração padrão
        cursor.execute("""
            INSERT INTO configuracoes (nome_hospital, rodape_empresa)
            VALUES ('Almoxarifado Hospitalar', 'Sistema de Gestão')
        """)
        
        # Criar almoxarifado padrão
        print("\n9. Criando almoxarifado padrão...")
        cursor.execute("""
            INSERT INTO almoxarifados (nome, descricao, ativo)
            VALUES ('Almoxarifado Principal', 'Almoxarifado principal do sistema', 1)
        """)
        almox_id = cursor.lastrowid
        print("   ✅ Almoxarifado Principal criado!")
        
        # Criar Super Admin
        print("\n10. Criando Super Administrador...")
        senha_hash = generate_password_hash('admin123')
        cursor.execute("""
            INSERT INTO usuarios (nome, username, senha, email, nivel_acesso, ativo)
            VALUES ('Administrador do Sistema', 'admin', ?, 'admin@hospital.com', 'admin_geral', 1)
        """, (senha_hash,))
        print("   ✅ Super Admin criado!")
        
        # Criar categorias padrão
        print("\n11. Criando categorias padrão...")
        categorias = [
            'Medicamentos',
            'Material Cirúrgico',
            'Material de Limpeza',
            'Equipamentos',
            'Descartáveis'
        ]
        for cat in categorias:
            cursor.execute("INSERT INTO categorias (nome) VALUES (?)", (cat,))
        print(f"   ✅ {len(categorias)} categorias criadas!")
        
        # Criar setores padrão
        print("\n12. Criando setores padrão...")
        setores = [
            'Enfermaria',
            'UTI',
            'Centro Cirúrgico',
            'Pronto Socorro',
            'Administração'
        ]
        for setor in setores:
            cursor.execute("INSERT INTO setores (nome, ativo) VALUES (?, 1)", (setor,))
        print(f"   ✅ {len(setores)} setores criados!")
        
        conn.commit()
    
    conn.close()
    
    print()
    print("=" * 70)
    print("✅ SISTEMA INICIALIZADO COM SUCESSO!")
    print("=" * 70)
    print()
    print("👑 SUPER ADMINISTRADOR CRIADO:")
    print("   Usuário: admin")
    print("   Senha: admin123")
    print()
    print("📝 PRÓXIMOS PASSOS:")
    print("   1. Inicie o servidor:")
    print("      cd backend")
    print("      python app.py")
    print()
    print("   2. Acesse: http://localhost:5000")
    print()
    print("   3. Faça login com: admin / admin123")
    print()
    print("   4. Vá em: Cadastros → Almoxarifados")
    print()
    print("   5. Clique em: [+ Novo Almoxarifado] ✨")
    print()
    print("🎉 PRONTO PARA USAR!")
    print()
    
except Exception as e:
    print()
    print(f"❌ ERRO: {str(e)}")
    import traceback
    traceback.print_exc()
    print()
    print("💡 Se o erro persistir, exclua o arquivo:")
    print("   backend/almoxarifado.db")
    print("   E execute este script novamente.")

input("\nPressione ENTER para sair...")
