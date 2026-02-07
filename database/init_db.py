"""
Script de Inicialização do Banco de Dados
Cria todas as tabelas e dados iniciais
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from backend.app import app, db
from backend.models import Usuario, Setor, Categoria, Fornecedor

def inicializar_banco():
    """Cria o banco de dados e dados iniciais"""
    
    print("=" * 60)
    print("INICIALIZANDO BANCO DE DADOS")
    print("=" * 60)
    
    with app.app_context():
        # Criar todas as tabelas
        print("\n1. Criando estrutura do banco de dados...")
        db.create_all()
        print("   ✓ Tabelas criadas com sucesso!")
        
        # Verificar se já existe usuário admin
        if Usuario.query.filter_by(username='admin').first():
            print("\n⚠ Usuário admin já existe. Pulando criação de dados iniciais.")
            return
        
        # Criar usuário administrador padrão
        print("\n2. Criando usuário Super Administrador...")
        admin = Usuario(
            nome='Administrador do Sistema',
            username='admin',
            email='admin@hospital.com',
            nivel_acesso='admin_geral'  # SUPER ADMIN por padrão!
        )
        admin.set_senha('admin123')
        db.session.add(admin)
        print("   ✓ Super Admin criado: admin / admin123")
        
        # Criar usuário almoxarife padrão
        print("\n3. Criando usuário almoxarife...")
        almoxarife = Usuario(
            nome='João Silva - Almoxarife',
            username='almoxarife',
            email='almoxarife@hospital.com',
            nivel_acesso='almoxarife'
        )
        almoxarife.set_senha('almox123')
        db.session.add(almoxarife)
        print("   ✓ Almoxarife criado: almoxarife / almox123")
        
        # Criar usuário visualização
        print("\n4. Criando usuário de visualização...")
        visualizador = Usuario(
            nome='Maria Santos - Visualização',
            username='usuario',
            email='usuario@hospital.com',
            nivel_acesso='visualizacao'
        )
        visualizador.set_senha('user123')
        db.session.add(visualizador)
        print("   ✓ Usuário criado: usuario / user123")
        
        # Criar setores padrão
        print("\n5. Criando setores padrão...")
        setores = [
            Setor(nome='Emergência', descricao='Setor de Emergência', responsavel='Dr. Carlos Souza'),
            Setor(nome='UTI', descricao='Unidade de Terapia Intensiva', responsavel='Dra. Ana Paula'),
            Setor(nome='Centro Cirúrgico', descricao='Bloco Cirúrgico', responsavel='Dr. Roberto Lima'),
            Setor(nome='Enfermaria', descricao='Enfermarias Gerais', responsavel='Enf. Juliana Costa'),
            Setor(nome='Farmácia', descricao='Farmácia Hospitalar', responsavel='Farm. Pedro Alves'),
        ]
        
        for setor in setores:
            db.session.add(setor)
        print(f"   ✓ {len(setores)} setores criados")
        
        # Criar categorias padrão
        print("\n6. Criando categorias padrão...")
        categorias = [
            Categoria(nome='Medicamentos', descricao='Medicamentos e fármacos'),
            Categoria(nome='Material Cirúrgico', descricao='Instrumentos e materiais cirúrgicos'),
            Categoria(nome='Material de Curativo', descricao='Gazes, ataduras, etc.'),
            Categoria(nome='Equipamentos', descricao='Equipamentos médicos'),
            Categoria(nome='Material de Consumo', descricao='Materiais descartáveis'),
            Categoria(nome='EPI', descricao='Equipamentos de Proteção Individual'),
        ]
        
        for categoria in categorias:
            db.session.add(categoria)
        print(f"   ✓ {len(categorias)} categorias criadas")
        
        # Criar fornecedores padrão
        print("\n7. Criando fornecedores padrão...")
        fornecedores = [
            Fornecedor(
                nome='MedSupply Distribuidora',
                cnpj='12.345.678/0001-90',
                contato='Carlos Santos',
                telefone='(11) 3456-7890',
                email='vendas@medsupply.com.br'
            ),
            Fornecedor(
                nome='Pharma Brasil Ltda',
                cnpj='98.765.432/0001-10',
                contato='Ana Silva',
                telefone='(11) 9876-5432',
                email='comercial@pharmabrasil.com.br'
            ),
            Fornecedor(
                nome='Cirúrgica Premium',
                cnpj='11.222.333/0001-44',
                contato='Roberto Lima',
                telefone='(11) 1234-5678',
                email='atendimento@cirurgicapremium.com.br'
            ),
        ]
        
        for fornecedor in fornecedores:
            db.session.add(fornecedor)
        print(f"   ✓ {len(fornecedores)} fornecedores criados")
        
        # Commit de todas as alterações
        print("\n8. Salvando dados no banco...")
        db.session.commit()
        print("   ✓ Dados salvos com sucesso!")
        
        print("\n" + "=" * 60)
        print("BANCO DE DADOS INICIALIZADO COM SUCESSO!")
        print("=" * 60)
        print("\nCredenciais de acesso:")
        print("\n  ADMINISTRADOR:")
        print("    Usuário: admin")
        print("    Senha: admin123")
        print("\n  ALMOXARIFE:")
        print("    Usuário: almoxarife")
        print("    Senha: almox123")
        print("\n  VISUALIZAÇÃO:")
        print("    Usuário: usuario")
        print("    Senha: user123")
        print("\n" + "=" * 60)


if __name__ == '__main__':
    try:
        inicializar_banco()
    except Exception as e:
        print(f"\n❌ ERRO ao inicializar banco de dados: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
