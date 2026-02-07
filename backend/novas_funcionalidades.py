"""
Novas funcionalidades do Sistema de Almoxarifado
- Backup manual e automático
- Edição de senha de usuários
- Configurações do sistema (logo, cores, rodapé)
- Busca avançada
- Gráficos e estatísticas
"""

import os
import shutil
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import db, Usuario, Item, Movimentacao, Setor, Configuracao, Categoria
from sqlalchemy import or_, func
from werkzeug.utils import secure_filename

# Blueprint para novas funcionalidades
novas_rotas = Blueprint('novas_rotas', __name__)


# ====================
# BACKUP DO SISTEMA
# ====================
@novas_rotas.route('/backup/manual')
@login_required
def backup_manual():
    """Gera backup manual do banco de dados"""
    if current_user.nivel_acesso != 'admin':
        flash('Apenas administradores podem fazer backup.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        # Descobrir o caminho real do banco de dados através do SQLAlchemy
        from sqlalchemy import inspect
        from app import db
        
        # Obter URI do banco
        db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        # Extrair caminho do arquivo (remover sqlite:///)
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
            # Se for caminho relativo, converter para absoluto
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
        else:
            flash('Tipo de banco não suportado para backup automático.', 'warning')
            return redirect(url_for('novas_rotas.configuracoes'))
        
        # Verificar se o banco existe
        if not os.path.exists(db_path):
            flash(f'Banco de dados não encontrado em: {db_path}', 'danger')
            flash('Verifique se o sistema está funcionando corretamente.', 'warning')
            return redirect(url_for('novas_rotas.configuracoes'))
        
        # Nome do arquivo de backup
        data_hora = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_backup = f'backup_almoxarifado_{data_hora}.db'
        
        # Criar pasta de backups se não existir (na mesma pasta do banco)
        db_dir = os.path.dirname(db_path)
        backup_folder = os.path.join(db_dir, 'backups')
        os.makedirs(backup_folder, exist_ok=True)
        
        caminho_backup = os.path.join(backup_folder, nome_backup)
        
        # Copiar banco de dados
        shutil.copy2(db_path, caminho_backup)
        
        # Atualizar última data de backup nas configurações
        config = Configuracao.query.first()
        if config:
            config.ultimo_backup = datetime.now()
            db.session.commit()
        
        flash(f'Backup criado com sucesso: {nome_backup}', 'success')
        flash(f'Salvo em: {backup_folder}', 'info')
        
        # Enviar arquivo para download
        return send_file(
            caminho_backup,
            as_attachment=True,
            download_name=nome_backup,
            mimetype='application/x-sqlite3'
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        flash(f'Erro ao criar backup: {str(e)}', 'danger')
        print(f"Erro detalhado:\n{error_details}")
        return redirect(url_for('novas_rotas.configuracoes'))


@novas_rotas.route('/backup/listar')
@login_required
def listar_backups():
    """Lista todos os backups disponíveis"""
    if current_user.nivel_acesso != 'admin':
        flash('Acesso negado.', 'danger')
        return redirect(url_for('dashboard'))
    
    backups = []
    if os.path.exists('backups'):
        for arquivo in os.listdir('backups'):
            if arquivo.endswith('.db'):
                caminho = os.path.join('backups', arquivo)
                tamanho = os.path.getsize(caminho)
                data_criacao = datetime.fromtimestamp(os.path.getctime(caminho))
                
                backups.append({
                    'nome': arquivo,
                    'tamanho': f'{tamanho / 1024:.2f} KB',
                    'data': data_criacao.strftime('%d/%m/%Y %H:%M')
                })
    
    return render_template('backup/listar.html', backups=backups)


# ====================
# EDITAR SENHA DE USUÁRIOS
# ====================
@novas_rotas.route('/usuarios/<int:id>/editar-senha', methods=['GET', 'POST'])
@login_required
def editar_senha_usuario(id):
    """Permite admin editar senha de qualquer usuário"""
    if current_user.nivel_acesso != 'admin':
        flash('Apenas administradores podem editar senhas de outros usuários.', 'danger')
        return redirect(url_for('dashboard'))
    
    usuario = Usuario.query.get_or_404(id)
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')
        
        if nova_senha != confirma_senha:
            flash('As senhas não coincidem!', 'danger')
        elif len(nova_senha) < 4:
            flash('A senha deve ter pelo menos 4 caracteres.', 'warning')
        else:
            usuario.set_senha(nova_senha)
            db.session.commit()
            flash(f'Senha do usuário {usuario.nome} alterada com sucesso!', 'success')
            return redirect(url_for('listar_usuarios'))
    
    return render_template('usuarios/editar_senha.html', usuario=usuario)


# ====================
# BLOQUEAR USUÁRIO
# ====================
@novas_rotas.route('/usuarios/<int:id>/bloquear', methods=['POST'])
@login_required
def bloquear_usuario(id):
    """Bloqueia/Desbloqueia um usuário"""
    if current_user.nivel_acesso != 'admin':
        flash('Apenas administradores podem bloquear usuários.', 'danger')
        return redirect(url_for('dashboard'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # Não permitir bloquear a si mesmo
    if usuario.id == current_user.id:
        flash('Você não pode bloquear a si mesmo!', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    # Alternar status
    usuario.ativo = not usuario.ativo
    db.session.commit()
    
    status = 'desbloqueado' if usuario.ativo else 'bloqueado'
    flash(f'Usuário {usuario.nome} foi {status} com sucesso!', 'success')
    
    return redirect(url_for('listar_usuarios'))


# ====================
# EXCLUIR USUÁRIO
# ====================
@novas_rotas.route('/usuarios/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_usuario(id):
    """Exclui permanentemente um usuário"""
    if current_user.nivel_acesso != 'admin':
        flash('Apenas administradores podem excluir usuários.', 'danger')
        return redirect(url_for('dashboard'))
    
    usuario = Usuario.query.get_or_404(id)
    
    # Não permitir excluir a si mesmo
    if usuario.id == current_user.id:
        flash('Você não pode excluir a si mesmo!', 'danger')
        return redirect(url_for('listar_usuarios'))
    
    # Verificar se o usuário tem movimentações
    if usuario.movimentacoes:
        flash(f'Não é possível excluir {usuario.nome} pois existem movimentações registradas por ele. Use a opção "Bloquear" em vez disso.', 'warning')
        return redirect(url_for('listar_usuarios'))
    
    nome = usuario.nome
    db.session.delete(usuario)
    db.session.commit()
    
    flash(f'Usuário {nome} foi excluído permanentemente!', 'success')
    return redirect(url_for('listar_usuarios'))


# ====================
# CONFIGURAÇÕES DO SISTEMA
# ====================
@novas_rotas.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    """Configurações gerais do sistema (admin_geral e admin)"""
    if current_user.nivel_acesso not in ['admin_geral', 'admin']:
        flash('Apenas administradores podem acessar as configurações.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Buscar ou criar configuração
    config = Configuracao.query.first()
    if not config:
        config = Configuracao()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        try:
            config.nome_hospital = request.form.get('nome_hospital')
            config.cor_primaria = request.form.get('cor_primaria')
            config.cor_secundaria = request.form.get('cor_secundaria')
            config.cor_navbar = request.form.get('cor_navbar', '#212529')
            config.cor_sucesso = request.form.get('cor_sucesso', '#198754')
            config.rodape_empresa = request.form.get('rodape_empresa')
            config.rodape_contato = request.form.get('rodape_contato')
            config.rodape_instagram = request.form.get('rodape_instagram')
            
            # Upload de logo
            if 'logo' in request.files:
                logo = request.files['logo']
                if logo and logo.filename:
                    # Verificar extensão
                    extensoes_permitidas = {'png', 'jpg', 'jpeg', 'svg', 'gif'}
                    extensao = logo.filename.rsplit('.', 1)[1].lower() if '.' in logo.filename else ''
                    
                    if extensao in extensoes_permitidas:
                        # Salvar com nome único
                        from werkzeug.utils import secure_filename
                        filename = f"logo.{extensao}"
                        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        
                        # Deletar logo antiga se existir
                        if config.logo_url:
                            old_logo = os.path.join(current_app.config['UPLOAD_FOLDER'], 
                                                   os.path.basename(config.logo_url))
                            if os.path.exists(old_logo):
                                os.remove(old_logo)
                        
                        logo.save(filepath)
                        config.logo_url = f'/static/uploads/{filename}'
                    else:
                        flash('Formato de imagem não permitido. Use PNG, JPG, SVG ou GIF.', 'warning')
            
            db.session.commit()
            flash('Configurações salvas com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao salvar configurações: {str(e)}', 'danger')
    
    return render_template('configuracoes/index.html', config=config)


# ====================
# BUSCA AVANÇADA
# ====================
@novas_rotas.route('/buscar')
@login_required
def buscar():
    """Busca avançada de itens por código de barras, nome ou lote"""
    termo = request.args.get('q', '').strip()
    
    if not termo:
        flash('Digite algo para buscar.', 'warning')
        return redirect(url_for('listar_itens'))
    
    # Buscar em código de barras, nome ou lote
    itens = Item.query.filter(
        Item.ativo == True,
        or_(
            Item.codigo_barras.ilike(f'%{termo}%'),
            Item.nome.ilike(f'%{termo}%'),
            Item.lote.ilike(f'%{termo}%')
        )
    ).all()
    
    return render_template('itens/buscar.html', itens=itens, termo=termo)


# ====================
# API PARA GRÁFICOS
# ====================
@novas_rotas.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """Retorna estatísticas para gráficos do dashboard"""
    
    # Itens por categoria
    categorias_stats = db.session.query(
        Categoria.nome,
        func.count(Item.id).label('total')
    ).join(Item).filter(Item.ativo == True).group_by(Categoria.nome).all()
    
    # Movimentações dos últimos 30 dias
    data_limite = datetime.now() - timedelta(days=30)
    movimentacoes_mes = db.session.query(
        func.date(Movimentacao.data_hora).label('data'),
        Movimentacao.tipo,
        func.count(Movimentacao.id).label('total')
    ).filter(Movimentacao.data_hora >= data_limite).group_by(
        func.date(Movimentacao.data_hora), Movimentacao.tipo
    ).all()
    
    # Consumo por setor (últimos 30 dias)
    consumo_setor = db.session.query(
        Setor.nome,
        func.sum(Movimentacao.quantidade).label('total')
    ).join(Movimentacao).filter(
        Movimentacao.tipo == 'saida',
        Movimentacao.data_hora >= data_limite
    ).group_by(Setor.nome).all()
    
    # Itens próximos do vencimento
    hoje = datetime.now().date()
    data_limite_validade = hoje + timedelta(days=30)
    itens_vencimento = db.session.query(
        func.count(Item.id)
    ).filter(
        Item.ativo == True,
        Item.data_validade.between(hoje, data_limite_validade)
    ).scalar()
    
    return jsonify({
        'categorias': [{'nome': c[0], 'total': c[1]} for c in categorias_stats],
        'movimentacoes': [{'data': str(m[0]), 'tipo': m[1], 'total': m[2]} for m in movimentacoes_mes],
        'consumo_setor': [{'setor': s[0], 'total': float(s[1])} for s in consumo_setor],
        'itens_vencimento': itens_vencimento
    })


# ====================
# ESTATÍSTICAS AVANÇADAS
# ====================
@novas_rotas.route('/relatorios/estatisticas')
@login_required
def estatisticas():
    """Página de estatísticas e gráficos"""
    
    # Total de itens
    total_itens = Item.query.filter_by(ativo=True).count()
    
    # Valor total do estoque (se tiver preços implementados)
    # Por enquanto, apenas quantidade
    total_estoque = db.session.query(
        func.sum(Item.estoque_atual)
    ).filter(Item.ativo == True).scalar() or 0
    
    # Movimentações do mês
    inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    movimentacoes_mes = Movimentacao.query.filter(
        Movimentacao.data_hora >= inicio_mes
    ).count()
    
    # Setores mais ativos
    setores_ativos = db.session.query(
        Setor.nome,
        func.count(Movimentacao.id).label('total')
    ).join(Movimentacao).filter(
        Movimentacao.tipo == 'saida',
        Movimentacao.data_hora >= inicio_mes
    ).group_by(Setor.nome).order_by(func.count(Movimentacao.id).desc()).limit(5).all()
    
    return render_template('relatorios/estatisticas.html',
                         total_itens=total_itens,
                         total_estoque=total_estoque,
                         movimentacoes_mes=movimentacoes_mes,
                         setores_ativos=setores_ativos)
