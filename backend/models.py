"""
Models do Sistema de Almoxarifado Hospitalar
Estrutura completa do banco de dados com relacionamentos
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ====================
# TABELA DE ALMOXARIFADOS
# ====================
class Almoxarifado(db.Model):
    """Diferentes locais/unidades do almoxarifado"""
    __tablename__ = 'almoxarifados'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    endereco = db.Column(db.String(300))
    responsavel = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    usuarios = db.relationship('Usuario', backref='almoxarifado', lazy=True)
    itens = db.relationship('Item', backref='almoxarifado', lazy=True)
    
    def __repr__(self):
        return f'<Almoxarifado {self.nome}>'


# ====================
# TABELA DE USUÁRIOS
# ====================
class Usuario(UserMixin, db.Model):
    """Usuários do sistema com controle de permissões"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100))
    
    # Níveis de acesso:
    # - admin_geral: Super admin (acessa TODOS os almoxarifados)
    # - admin: Administrador do seu almoxarifado
    # - almoxarife: Gerencia estoque do seu almoxarifado
    # - visualizacao: Apenas visualiza seu almoxarifado
    nivel_acesso = db.Column(db.String(20), nullable=False)
    
    # Almoxarifado ao qual o usuário pertence (NULL para admin_geral)
    almoxarifado_id = db.Column(db.Integer, db.ForeignKey('almoxarifados.id'))
    
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('Movimentacao', backref='usuario', lazy=True)
    
    def set_senha(self, senha):
        """Gera hash seguro da senha"""
        self.senha_hash = generate_password_hash(senha)
    
    def check_senha(self, senha):
        """Verifica se a senha está correta"""
        return check_password_hash(self.senha_hash, senha)
    
    def pode_acessar_almoxarifado(self, almoxarifado_id):
        """Verifica se o usuário pode acessar um almoxarifado específico"""
        # Super admin e admin central veem tudo
        if self.nivel_acesso in ['admin_geral', 'admin']:
            return True
        # Outros só veem seu almoxarifado
        return self.almoxarifado_id == almoxarifado_id
    
    @property
    def eh_admin_geral(self):
        """Verifica se é super administrador (cria almoxarifados e personaliza sistema)"""
        return self.nivel_acesso == 'admin_geral'
    
    @property
    def eh_admin(self):
        """Verifica se é admin (qualquer tipo)"""
        return self.nivel_acesso in ['admin_geral', 'admin', 'admin_local']
    
    @property
    def eh_admin_local(self):
        """Verifica se é administrador local (gerencia apenas seu almoxarifado)"""
        return self.nivel_acesso == 'admin_local'
    
    @property
    def pode_gerenciar_usuarios(self):
        """Verifica se pode gerenciar usuários (criar, editar, bloquear)"""
        # Admin geral e admin central: todos os usuários
        # Admin local: apenas usuários do seu almoxarifado
        return self.nivel_acesso in ['admin_geral', 'admin', 'admin_local']
    
    @property
    def pode_configurar_sistema(self):
        """Verifica se pode acessar configurações do sistema"""
        return self.nivel_acesso == 'admin_geral'
    
    @property
    def pode_gerenciar_estoque(self):
        """Verifica se pode fazer movimentações"""
        return self.nivel_acesso in ['admin_geral', 'admin', 'admin_local', 'almoxarife']
    
    @property
    def ve_todos_almoxarifados(self):
        """Verifica se vê todos os almoxarifados"""
        return self.nivel_acesso in ['admin_geral', 'admin']
    
    @property
    def nome_nivel_exibicao(self):
        """Retorna o nome amigável do nível de acesso"""
        niveis = {
            'admin_geral': 'Super Administrador',
            'admin': 'Administrador Central',
            'admin_local': 'Administrador Local',
            'almoxarife': 'Colaborador',
            'visualizacao': 'Visualizador'
        }
        return niveis.get(self.nivel_acesso, self.nivel_acesso)
    
    def __repr__(self):
        return f'<Usuario {self.username}>'


# ====================
# TABELA DE SETORES
# ====================
class Setor(db.Model):
    """Setores do hospital para controle de saídas"""
    __tablename__ = 'setores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    responsavel = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    movimentacoes = db.relationship('Movimentacao', backref='setor', lazy=True)
    
    def __repr__(self):
        return f'<Setor {self.nome}>'


# ====================
# TABELA DE CATEGORIAS
# ====================
class Categoria(db.Model):
    """Categorias de produtos"""
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    
    # Relacionamentos
    itens = db.relationship('Item', backref='categoria', lazy=True)
    
    def __repr__(self):
        return f'<Categoria {self.nome}>'


# ====================
# TABELA DE FORNECEDORES
# ====================
class Fornecedor(db.Model):
    """Fornecedores de materiais"""
    __tablename__ = 'fornecedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    cnpj = db.Column(db.String(18), unique=True)
    contato = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento removido pois não usamos mais fornecedor nos itens
    
    def __repr__(self):
        return f'<Fornecedor {self.nome}>'


# ====================
# TABELA DE ITENS
# ====================
class Item(db.Model):
    """Itens do almoxarifado"""
    __tablename__ = 'itens'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_barras = db.Column(db.String(50), nullable=False)  # Código de barras (pode repetir com lotes diferentes)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    marca = db.Column(db.String(100))  # NOVO: Marca do produto
    unidade_medida = db.Column(db.String(20), nullable=False)  # UN, CX, PCT, L, KG, etc
    estoque_minimo = db.Column(db.Float, default=0)
    estoque_atual = db.Column(db.Float, default=0)
    lote = db.Column(db.String(50), nullable=False)  # Obrigatório
    data_validade = db.Column(db.Date)
    
    # Histórico de compras (JSON string com datas e preços)
    historico_compras = db.Column(db.Text)  # NOVO: Armazena JSON com histórico
    
    # Chaves estrangeiras
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    almoxarifado_id = db.Column(db.Integer, db.ForeignKey('almoxarifados.id'), nullable=False)
    
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    movimentacoes = db.relationship('Movimentacao', backref='item', lazy=True)
    
    # Índice composto para garantir unicidade de codigo_barras+lote+almoxarifado
    __table_args__ = (
        db.UniqueConstraint('codigo_barras', 'lote', 'almoxarifado_id', name='uix_codigo_lote_almox'),
    )
    
    def __repr__(self):
        return f'<Item {self.codigo_barras} - Lote {self.lote} - {self.nome}>'
    
    @property
    def codigo_completo(self):
        """Retorna código com lote para identificação única"""
        return f"{self.codigo_barras}-{self.lote}"
    
    @property
    def status_estoque(self):
        """Retorna status do estoque: crítico, baixo, ok"""
        if self.estoque_atual <= 0:
            return 'zerado'
        elif self.estoque_atual < self.estoque_minimo * 0.5:
            return 'critico'
        elif self.estoque_atual < self.estoque_minimo:
            return 'baixo'
        else:
            return 'ok'
    
    @property
    def status_validade(self):
        """Retorna status da validade"""
        if not self.data_validade:
            return 'sem_validade'
        
        dias_restantes = (self.data_validade - datetime.now().date()).days
        
        if dias_restantes < 0:
            return 'vencido'
        elif dias_restantes <= 30:
            return 'vence_em_breve'
        else:
            return 'ok'


# ====================
# TABELA DE MOVIMENTAÇÕES
# ====================
class Movimentacao(db.Model):
    """Registro de todas as entradas e saídas"""
    __tablename__ = 'movimentacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)  # entrada, saida, ajuste
    quantidade = db.Column(db.Float, nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.Text)
    nota_fiscal = db.Column(db.String(50))
    
    # Chaves estrangeiras
    item_id = db.Column(db.Integer, db.ForeignKey('itens.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'))  # Apenas para saídas
    
    def __repr__(self):
        return f'<Movimentacao {self.tipo} - {self.quantidade}>'


# ====================
# TABELA DE CONFIGURAÇÕES DO SISTEMA
# ====================
class Configuracao(db.Model):
    """Configurações personalizáveis do sistema"""
    __tablename__ = 'configuracoes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_hospital = db.Column(db.String(200), default='Hospital')
    logo_url = db.Column(db.String(500))  # URL ou caminho da logo
    
    # Cores do tema (hexadecimal)
    cor_primaria = db.Column(db.String(7), default='#0d6efd')  # Botões, links
    cor_secundaria = db.Column(db.String(7), default='#6c757d')  # Títulos
    cor_navbar = db.Column(db.String(7), default='#212529')  # Fundo da navbar
    cor_sucesso = db.Column(db.String(7), default='#198754')  # Alertas de sucesso
    
    # Rodapé
    rodape_texto = db.Column(db.String(200), default='Todos os direitos reservados')
    rodape_empresa = db.Column(db.String(200), default='Eduardo Soluções Tecnológicas')
    rodape_contato = db.Column(db.String(100))
    rodape_instagram = db.Column(db.String(100))
    
    # Backup
    backup_automatico = db.Column(db.Boolean, default=False)
    backup_frequencia = db.Column(db.Integer, default=7)  # dias
    ultimo_backup = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Configuracao {self.nome_hospital}>'
