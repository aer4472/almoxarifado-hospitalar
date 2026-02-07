"""
Sistema de Almoxarifado Hospitalar
Aplicação principal Flask
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from io import BytesIO

# Importar models
from models import db, Usuario, Setor, Categoria, Fornecedor, Item, Movimentacao, Configuracao, Almoxarifado

# Importar gerador de relatórios
from relatorios import gerar_relatorio_estoque, gerar_relatorio_movimentacoes

# Importar novas funcionalidades
from novas_funcionalidades import novas_rotas
from almoxarifados import almoxarifados

# Carregar variáveis de ambiente
load_dotenv()

# Definir caminho absoluto do banco de dados
# O banco deve estar na raiz do projeto (um nível acima do backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'almoxarifado.db')

# Configuração da aplicação
app = Flask(__name__, 
            template_folder='../frontend/templates',
            static_folder='../frontend/static')

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-secreta-padrao')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', f'sqlite:///{DATABASE_PATH}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'frontend', 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Debug: Mostrar onde o banco está configurado
print(f"[INFO] Banco de dados configurado em: {DATABASE_PATH}")

# Inicializar extensões
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Registrar blueprint de novas funcionalidades
# Registrar blueprints
app.register_blueprint(novas_rotas)
app.register_blueprint(almoxarifados)

# ====================
# CONTEXT PROCESSOR
# ====================
@app.context_processor
def inject_config():
    """Injeta configurações em todos os templates"""
    config = Configuracao.query.first()
    if not config:
        config = Configuracao()
        db.session.add(config)
        db.session.commit()
    return dict(config_sistema=config)

# ====================
# CONFIGURAÇÃO DO LOGIN
# ====================
@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


# ====================
# DECORADOR DE PERMISSÕES
# ====================
def requer_permissao(*niveis):
    """Decorator para verificar nível de acesso"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Você precisa estar logado.', 'warning')
                return redirect(url_for('login'))
            
            if current_user.nivel_acesso not in niveis:
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ====================
# ROTAS DE AUTENTICAÇÃO
# ====================
@app.route('/')
def index():
    """Redireciona para login ou dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        senha = request.form.get('senha')
        
        usuario = Usuario.query.filter_by(username=username, ativo=True).first()
        
        if usuario and usuario.check_senha(senha):
            login_user(usuario)
            flash(f'Bem-vindo, {usuario.nome}!', 'success')
            
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Fazer logout"""
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))


# ====================
# DASHBOARD
# ====================
@app.route('/dashboard')
@login_required
def dashboard():
    """Painel principal com indicadores filtrados por almoxarifado"""
    
    # Base query para filtrar por almoxarifado
    base_query = Item.query.filter_by(ativo=True)
    
    # Filtrar por almoxarifado se não for admin geral/central
    if not current_user.ve_todos_almoxarifados:
        if current_user.almoxarifado_id:
            base_query = base_query.filter_by(almoxarifado_id=current_user.almoxarifado_id)
        else:
            base_query = base_query.filter_by(almoxarifado_id=None)
    
    # Estatísticas gerais
    total_itens = base_query.count()
    
    # Itens abaixo do estoque mínimo
    itens_baixo_estoque = base_query.filter(
        Item.estoque_atual < Item.estoque_minimo
    ).all()
    
    # Itens vencidos
    hoje = datetime.now().date()
    itens_vencidos = base_query.filter(
        Item.data_validade < hoje
    ).all()
    
    # Itens a vencer em 30 dias
    data_limite = hoje + timedelta(days=30)
    itens_a_vencer = base_query.filter(
        Item.data_validade.between(hoje, data_limite)
    ).all()
    
    # Últimas movimentações (filtradas por almoxarifado através dos itens)
    movimentacoes_query = Movimentacao.query
    
    if not current_user.ve_todos_almoxarifados and current_user.almoxarifado_id:
        # Pegar IDs dos itens do almoxarifado do usuário
        itens_ids = [item.id for item in base_query.all()]
        movimentacoes_query = movimentacoes_query.filter(Movimentacao.item_id.in_(itens_ids))
    
    ultimas_movimentacoes = movimentacoes_query.order_by(
        Movimentacao.data_hora.desc()
    ).limit(10).all()
    
    return render_template('dashboard.html',
                         total_itens=total_itens,
                         itens_baixo_estoque=itens_baixo_estoque,
                         itens_vencidos=itens_vencidos,
                         itens_a_vencer=itens_a_vencer,
                         ultimas_movimentacoes=ultimas_movimentacoes)


# ====================
# ROTAS DE ITENS
# ====================
@app.route('/itens')
@login_required
def listar_itens():
    """Lista itens filtrados por almoxarifado do usuário ou filtro selecionado"""
    # Pegar filtro de almoxarifado (se admin selecionar)
    almoxarifado_filtro = request.args.get('almoxarifado_id', '')
    
    # Filtrar por almoxarifado
    query = Item.query.filter_by(ativo=True)
    
    # Se admin selecionou um filtro específico
    if almoxarifado_filtro and current_user.ve_todos_almoxarifados:
        query = query.filter_by(almoxarifado_id=int(almoxarifado_filtro))
    # Se não é admin geral ou admin central, filtrar por almoxarifado do usuário
    elif not current_user.ve_todos_almoxarifados:
        if current_user.almoxarifado_id:
            query = query.filter_by(almoxarifado_id=current_user.almoxarifado_id)
        else:
            # Usuário sem almoxarifado não vê nada
            query = query.filter_by(almoxarifado_id=None)
    
    itens = query.order_by(Item.nome).all()
    
    # Buscar almoxarifados para o filtro (apenas para admins)
    almoxarifados = []
    if current_user.ve_todos_almoxarifados:
        almoxarifados = Almoxarifado.query.filter_by(ativo=True).order_by(Almoxarifado.nome).all()
    
    return render_template('itens/listar.html', 
                         itens=itens, 
                         almoxarifados=almoxarifados,
                         almoxarifado_selecionado=almoxarifado_filtro)


@app.route('/itens/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin', 'almoxarife')
def novo_item():
    """Cadastrar novo item"""
    if request.method == 'POST':
        try:
            # Determinar almoxarifado
            if current_user.ve_todos_almoxarifados:
                # Admin geral ou admin central: pode escolher
                almoxarifado_id = request.form.get('almoxarifado_id')
                if not almoxarifado_id:
                    flash('Selecione o almoxarifado!', 'warning')
                    categorias = Categoria.query.order_by(Categoria.nome).all()
                    almoxarifados = Almoxarifado.query.filter_by(ativo=True).order_by(Almoxarifado.nome).all()
                    return render_template('itens/form.html', categorias=categorias, almoxarifados=almoxarifados)
            else:
                # Admin local ou colaborador: usa o almoxarifado dele
                almoxarifado_id = current_user.almoxarifado_id
                if not almoxarifado_id:
                    flash('Você não está vinculado a nenhum almoxarifado! Contate o administrador.', 'danger')
                    return redirect(url_for('dashboard'))
            
            # Processar data de validade
            data_validade = None
            if request.form.get('data_validade'):
                data_validade = datetime.strptime(request.form.get('data_validade'), '%Y-%m-%d').date()
            
            item = Item(
                codigo_barras=request.form.get('codigo_barras'),
                nome=request.form.get('nome'),
                descricao=request.form.get('descricao'),
                marca=request.form.get('marca'),
                unidade_medida=request.form.get('unidade_medida'),
                estoque_minimo=float(request.form.get('estoque_minimo', 0)),
                lote=request.form.get('lote'),
                data_validade=data_validade,
                categoria_id=request.form.get('categoria_id') or None,
                almoxarifado_id=almoxarifado_id
            )
            
            db.session.add(item)
            db.session.commit()
            
            flash('Item cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_itens'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar item: {str(e)}', 'danger')
    
    categorias = Categoria.query.order_by(Categoria.nome).all()
    almoxarifados = Almoxarifado.query.filter_by(ativo=True).order_by(Almoxarifado.nome).all()
    
    return render_template('itens/form.html', 
                         categorias=categorias,
                         almoxarifados=almoxarifados)


@app.route('/itens/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin', 'almoxarife')
def editar_item(id):
    """Editar item existente"""
    item = Item.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Processar data de validade
            data_validade = None
            if request.form.get('data_validade'):
                data_validade = datetime.strptime(request.form.get('data_validade'), '%Y-%m-%d').date()
            
            item.codigo_barras = request.form.get('codigo_barras')
            item.nome = request.form.get('nome')
            item.descricao = request.form.get('descricao')
            item.marca = request.form.get('marca')
            item.unidade_medida = request.form.get('unidade_medida')
            item.estoque_minimo = float(request.form.get('estoque_minimo', 0))
            item.lote = request.form.get('lote')
            item.data_validade = data_validade
            item.categoria_id = request.form.get('categoria_id') or None
            
            # Atualizar almoxarifado (apenas admin geral e admin central podem)
            if current_user.ve_todos_almoxarifados:
                almoxarifado_id = request.form.get('almoxarifado_id')
                if almoxarifado_id:
                    item.almoxarifado_id = almoxarifado_id
            
            db.session.commit()
            
            flash('Item atualizado com sucesso!', 'success')
            return redirect(url_for('listar_itens'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar item: {str(e)}', 'danger')
    
    categorias = Categoria.query.order_by(Categoria.nome).all()
    almoxarifados = Almoxarifado.query.filter_by(ativo=True).order_by(Almoxarifado.nome).all()
    
    return render_template('itens/form.html', 
                         item=item,
                         categorias=categorias,
                         almoxarifados=almoxarifados)


@app.route('/itens/<int:id>/excluir', methods=['POST'])
@login_required
@requer_permissao('admin')
def excluir_item(id):
    """Excluir item (soft delete)"""
    item = Item.query.get_or_404(id)
    item.ativo = False
    db.session.commit()
    
    flash('Item excluído com sucesso!', 'success')
    return redirect(url_for('listar_itens'))


# ====================
# ROTAS DE MOVIMENTAÇÕES
# ====================
@app.route('/movimentacoes')
@login_required
def listar_movimentacoes():
    """Lista movimentações filtradas por almoxarifado"""
    page = request.args.get('page', 1, type=int)
    almoxarifado_filtro = request.args.get('almoxarifado_id', '')
    
    # Base query
    query = Movimentacao.query
    
    # Se admin selecionou um filtro específico
    if almoxarifado_filtro and current_user.ve_todos_almoxarifados:
        # Pegar IDs dos itens do almoxarifado filtrado
        itens_almoxarifado = Item.query.filter_by(
            almoxarifado_id=int(almoxarifado_filtro)
        ).all()
        itens_ids = [item.id for item in itens_almoxarifado]
        
        if itens_ids:
            query = query.filter(Movimentacao.item_id.in_(itens_ids))
    # Se não é admin geral/central, filtrar por almoxarifado do usuário
    elif not current_user.ve_todos_almoxarifados and current_user.almoxarifado_id:
        # Pegar IDs dos itens do almoxarifado do usuário
        itens_almoxarifado = Item.query.filter_by(
            almoxarifado_id=current_user.almoxarifado_id
        ).all()
        itens_ids = [item.id for item in itens_almoxarifado]
        
        # Filtrar movimentações desses itens
        query = query.filter(Movimentacao.item_id.in_(itens_ids))
    
    movimentacoes = query.order_by(
        Movimentacao.data_hora.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    # Buscar almoxarifados para o filtro (apenas para admins)
    almoxarifados = []
    if current_user.ve_todos_almoxarifados:
        almoxarifados = Almoxarifado.query.filter_by(ativo=True).order_by(Almoxarifado.nome).all()
    
    return render_template('movimentacoes/listar.html', 
                         movimentacoes=movimentacoes,
                         almoxarifados=almoxarifados,
                         almoxarifado_selecionado=almoxarifado_filtro)


@app.route('/movimentacoes/entrada', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin', 'almoxarife')
def entrada_material():
    """Registrar entrada de material"""
    if request.method == 'POST':
        try:
            item_id = int(request.form.get('item_id'))
            quantidade = float(request.form.get('quantidade'))
            
            item = Item.query.get_or_404(item_id)
            
            # Criar movimentação
            movimentacao = Movimentacao(
                tipo='entrada',
                quantidade=quantidade,
                observacao=request.form.get('observacao'),
                nota_fiscal=request.form.get('nota_fiscal'),
                item_id=item_id,
                usuario_id=current_user.id
            )
            
            # Atualizar estoque
            item.estoque_atual += quantidade
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash(f'Entrada registrada! Estoque atual: {item.estoque_atual} {item.unidade_medida}', 'success')
            return redirect(url_for('listar_movimentacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar entrada: {str(e)}', 'danger')
    
    # Filtrar itens por almoxarifado
    query = Item.query.filter_by(ativo=True)
    
    if not current_user.ve_todos_almoxarifados:
        if current_user.almoxarifado_id:
            query = query.filter_by(almoxarifado_id=current_user.almoxarifado_id)
        else:
            query = query.filter_by(almoxarifado_id=None)
    
    itens = query.order_by(Item.nome).all()
    return render_template('movimentacoes/entrada.html', itens=itens)


@app.route('/movimentacoes/saida', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin', 'almoxarife')
def saida_material():
    """Registrar saída de material"""
    if request.method == 'POST':
        try:
            item_id = int(request.form.get('item_id'))
            quantidade = float(request.form.get('quantidade'))
            setor_id = int(request.form.get('setor_id'))
            
            item = Item.query.get_or_404(item_id)
            
            # Verificar se há estoque suficiente
            if item.estoque_atual < quantidade:
                flash('Estoque insuficiente!', 'danger')
                return redirect(url_for('saida_material'))
            
            # Criar movimentação
            movimentacao = Movimentacao(
                tipo='saida',
                quantidade=quantidade,
                observacao=request.form.get('observacao'),
                item_id=item_id,
                usuario_id=current_user.id,
                setor_id=setor_id
            )
            
            # Atualizar estoque
            item.estoque_atual -= quantidade
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash(f'Saída registrada! Estoque atual: {item.estoque_atual} {item.unidade_medida}', 'success')
            return redirect(url_for('listar_movimentacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar saída: {str(e)}', 'danger')
    
    # Filtrar itens por almoxarifado
    query = Item.query.filter_by(ativo=True)
    
    if not current_user.ve_todos_almoxarifados:
        if current_user.almoxarifado_id:
            query = query.filter_by(almoxarifado_id=current_user.almoxarifado_id)
        else:
            query = query.filter_by(almoxarifado_id=None)
    
    itens = query.order_by(Item.nome).all()
    setores = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()
    
    return render_template('movimentacoes/saida.html', itens=itens, setores=setores)


@app.route('/movimentacoes/ajuste', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin', 'almoxarife')
def ajuste_estoque():
    """Ajuste manual de estoque (inventário)"""
    if request.method == 'POST':
        try:
            item_id = int(request.form.get('item_id'))
            nova_quantidade = float(request.form.get('nova_quantidade'))
            
            item = Item.query.get_or_404(item_id)
            
            # Calcular diferença
            diferenca = nova_quantidade - item.estoque_atual
            
            # Criar movimentação
            movimentacao = Movimentacao(
                tipo='ajuste',
                quantidade=diferenca,
                observacao=request.form.get('observacao'),
                item_id=item_id,
                usuario_id=current_user.id
            )
            
            # Atualizar estoque
            item.estoque_atual = nova_quantidade
            
            db.session.add(movimentacao)
            db.session.commit()
            
            flash(f'Ajuste registrado! Estoque ajustado para: {item.estoque_atual} {item.unidade_medida}', 'success')
            return redirect(url_for('listar_movimentacoes'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar ajuste: {str(e)}', 'danger')
    
    # Filtrar itens por almoxarifado
    query = Item.query.filter_by(ativo=True)
    
    if not current_user.ve_todos_almoxarifados:
        if current_user.almoxarifado_id:
            query = query.filter_by(almoxarifado_id=current_user.almoxarifado_id)
        else:
            query = query.filter_by(almoxarifado_id=None)
    
    itens = query.order_by(Item.nome).all()
    return render_template('movimentacoes/ajuste.html', itens=itens)


# ====================
# ROTAS DE SETORES
# ====================
@app.route('/setores')
@login_required
def listar_setores():
    """Lista todos os setores"""
    setores = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()
    return render_template('setores/listar.html', setores=setores)


@app.route('/setores/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin')
def novo_setor():
    """Cadastrar novo setor"""
    if request.method == 'POST':
        try:
            setor = Setor(
                nome=request.form.get('nome'),
                descricao=request.form.get('descricao'),
                responsavel=request.form.get('responsavel')
            )
            
            db.session.add(setor)
            db.session.commit()
            
            flash('Setor cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_setores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar setor: {str(e)}', 'danger')
    
    return render_template('setores/form.html')


@app.route('/setores/<int:id>/editar', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin')
def editar_setor(id):
    """Editar setor existente"""
    setor = Setor.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            setor.nome = request.form.get('nome')
            setor.descricao = request.form.get('descricao')
            setor.responsavel = request.form.get('responsavel')
            
            db.session.commit()
            
            flash('Setor atualizado com sucesso!', 'success')
            return redirect(url_for('listar_setores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar setor: {str(e)}', 'danger')
    
    return render_template('setores/form.html', setor=setor)


@app.route('/setores/<int:id>/excluir', methods=['POST'])
@login_required
@requer_permissao('admin')
def excluir_setor(id):
    """Excluir setor"""
    setor = Setor.query.get_or_404(id)
    setor.ativo = False
    db.session.commit()
    
    flash('Setor excluído com sucesso!', 'success')
    return redirect(url_for('listar_setores'))


# ====================
# ROTAS DE CATEGORIAS
# ====================
@app.route('/categorias')
@login_required
def listar_categorias():
    """Lista todas as categorias"""
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return render_template('categorias/listar.html', categorias=categorias)


@app.route('/categorias/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin')
def nova_categoria():
    """Cadastrar nova categoria"""
    if request.method == 'POST':
        try:
            categoria = Categoria(
                nome=request.form.get('nome'),
                descricao=request.form.get('descricao')
            )
            
            db.session.add(categoria)
            db.session.commit()
            
            flash('Categoria cadastrada com sucesso!', 'success')
            return redirect(url_for('listar_categorias'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar categoria: {str(e)}', 'danger')
    
    return render_template('categorias/form.html')


# ====================
# ROTAS DE FORNECEDORES
# ====================
@app.route('/fornecedores')
@login_required
def listar_fornecedores():
    """Lista todos os fornecedores"""
    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome).all()
    return render_template('fornecedores/listar.html', fornecedores=fornecedores)


@app.route('/fornecedores/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin')
def novo_fornecedor():
    """Cadastrar novo fornecedor"""
    if request.method == 'POST':
        try:
            fornecedor = Fornecedor(
                nome=request.form.get('nome'),
                cnpj=request.form.get('cnpj'),
                contato=request.form.get('contato'),
                telefone=request.form.get('telefone'),
                email=request.form.get('email')
            )
            
            db.session.add(fornecedor)
            db.session.commit()
            
            flash('Fornecedor cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_fornecedores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar fornecedor: {str(e)}', 'danger')
    
    return render_template('fornecedores/form.html')


# ====================
# ROTAS DE USUÁRIOS
# ====================
@app.route('/usuarios')
@login_required
@requer_permissao('admin_geral', 'admin')
def listar_usuarios():
    """Lista todos os usuários"""
    usuarios = Usuario.query.filter_by(ativo=True).order_by(Usuario.nome).all()
    return render_template('usuarios/listar.html', usuarios=usuarios)


@app.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@requer_permissao('admin_geral', 'admin')
def novo_usuario():
    """Cadastrar novo usuário"""
    if request.method == 'POST':
        try:
            # Obter almoxarifado_id se fornecido
            almoxarifado_id = request.form.get('almoxarifado_id')
            if almoxarifado_id == '':
                almoxarifado_id = None
            
            usuario = Usuario(
                nome=request.form.get('nome'),
                username=request.form.get('username'),
                email=request.form.get('email'),
                nivel_acesso=request.form.get('nivel_acesso'),
                almoxarifado_id=almoxarifado_id
            )
            usuario.set_senha(request.form.get('senha'))
            
            db.session.add(usuario)
            db.session.commit()
            
            flash('Usuário cadastrado com sucesso!', 'success')
            return redirect(url_for('listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar usuário: {str(e)}', 'danger')
    
    # Buscar almoxarifados para o formulário
    almoxarifados = Almoxarifado.query.filter_by(ativo=True).order_by(Almoxarifado.nome).all()
    return render_template('usuarios/form.html', almoxarifados=almoxarifados)


# ====================
# ROTAS DE RELATÓRIOS
# ====================
@app.route('/relatorios')
@login_required
def relatorios():
    """Página de relatórios"""
    return render_template('relatorios/index.html')


@app.route('/relatorios/estoque-pdf')
@login_required
def relatorio_estoque_pdf():
    """Gerar relatório de estoque em PDF filtrado por almoxarifado"""
    pdf = gerar_relatorio_estoque(current_user)
    
    return send_file(
        BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'relatorio_estoque_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )


@app.route('/relatorios/movimentacoes-pdf')
@login_required
def relatorio_movimentacoes_pdf():
    """Gerar relatório de movimentações em PDF filtrado por almoxarifado"""
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    pdf = gerar_relatorio_movimentacoes(current_user, data_inicio, data_fim)
    
    return send_file(
        BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'relatorio_movimentacoes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )


# ====================
# API ENDPOINTS
# ====================
@app.route('/api/item/<int:id>')
@login_required
def api_item(id):
    """API para obter dados de um item"""
    item = Item.query.get_or_404(id)
    
    return jsonify({
        'id': item.id,
        'codigo_barras': item.codigo_barras,
        'nome': item.nome,
        'estoque_atual': item.estoque_atual,
        'unidade_medida': item.unidade_medida,
        'estoque_minimo': item.estoque_minimo
    })


# ====================
# TRATAMENTO DE ERROS
# ====================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('erro.html', erro='Página não encontrada'), 404


@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('erro.html', erro='Erro interno do servidor'), 500


# ====================
# EXECUÇÃO
# ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Criar usuário admin padrão se não existir
        if not Usuario.query.filter_by(username='admin').first():
            admin = Usuario(
                nome='Administrador',
                username='admin',
                nivel_acesso='admin'
            )
            admin.set_senha('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Usuário admin criado: admin / admin123')
    
    app.run(debug=True, host='0.0.0.0', port=5000)
