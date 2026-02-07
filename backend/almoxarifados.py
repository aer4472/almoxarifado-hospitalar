"""
Rotas para gestão de almoxarifados
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Almoxarifado
from datetime import datetime

almoxarifados = Blueprint('almoxarifados', __name__)


def requer_admin():
    """Verificar se usuário é admin ou admin_geral"""
    if current_user.nivel_acesso not in ['admin_geral', 'admin']:
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return False
    return True


@almoxarifados.route('/almoxarifados')
@login_required
def listar():
    """Listar todos os almoxarifados"""
    if not requer_admin():
        return redirect(url_for('dashboard'))
    
    almoxarifados_lista = Almoxarifado.query.order_by(Almoxarifado.nome).all()
    return render_template('almoxarifados/listar.html', almoxarifados=almoxarifados_lista)


@almoxarifados.route('/almoxarifados/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Cadastrar novo almoxarifado (admin_geral ou admin)"""
    if current_user.nivel_acesso not in ['admin_geral', 'admin']:
        flash('Apenas administradores podem criar almoxarifados.', 'danger')
        return redirect(url_for('almoxarifados.listar'))
    
    if request.method == 'POST':
        try:
            # Verificar se já existe
            nome = request.form.get('nome')
            if Almoxarifado.query.filter_by(nome=nome).first():
                flash('Já existe um almoxarifado com este nome!', 'warning')
                return redirect(url_for('almoxarifados.novo'))
            
            almoxarifado = Almoxarifado(
                nome=nome,
                descricao=request.form.get('descricao'),
                endereco=request.form.get('endereco'),
                responsavel=request.form.get('responsavel'),
                telefone=request.form.get('telefone'),
                ativo=True
            )
            
            db.session.add(almoxarifado)
            db.session.commit()
            
            flash(f'Almoxarifado "{almoxarifado.nome}" cadastrado com sucesso!', 'success')
            return redirect(url_for('almoxarifados.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar almoxarifado: {str(e)}', 'danger')
    
    return render_template('almoxarifados/form.html')


@almoxarifados.route('/almoxarifados/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Editar almoxarifado existente"""
    if not requer_admin():
        return redirect(url_for('dashboard'))
    
    almoxarifado = Almoxarifado.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Verificar nome duplicado (exceto o próprio)
            nome = request.form.get('nome')
            duplicado = Almoxarifado.query.filter(
                Almoxarifado.nome == nome,
                Almoxarifado.id != id
            ).first()
            
            if duplicado:
                flash('Já existe outro almoxarifado com este nome!', 'warning')
                return redirect(url_for('almoxarifados.editar', id=id))
            
            almoxarifado.nome = nome
            almoxarifado.descricao = request.form.get('descricao')
            almoxarifado.endereco = request.form.get('endereco')
            almoxarifado.responsavel = request.form.get('responsavel')
            almoxarifado.telefone = request.form.get('telefone')
            
            db.session.commit()
            
            flash(f'Almoxarifado "{almoxarifado.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('almoxarifados.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar almoxarifado: {str(e)}', 'danger')
    
    return render_template('almoxarifados/form.html', almoxarifado=almoxarifado)


@almoxarifados.route('/almoxarifados/<int:id>/ativar-desativar')
@login_required
def ativar_desativar(id):
    """Ativar/desativar almoxarifado (apenas admin_geral)"""
    if current_user.nivel_acesso != 'admin_geral':
        flash('Apenas o super administrador pode ativar/desativar almoxarifados.', 'danger')
        return redirect(url_for('almoxarifados.listar'))
    
    almoxarifado = Almoxarifado.query.get_or_404(id)
    
    try:
        almoxarifado.ativo = not almoxarifado.ativo
        db.session.commit()
        
        status = "ativado" if almoxarifado.ativo else "desativado"
        flash(f'Almoxarifado "{almoxarifado.nome}" {status} com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao alterar status: {str(e)}', 'danger')
    
    return redirect(url_for('almoxarifados.listar'))


@almoxarifados.route('/almoxarifados/<int:id>/excluir')
@login_required
def excluir(id):
    """Excluir almoxarifado (apenas admin_geral, com validações)"""
    if current_user.nivel_acesso != 'admin_geral':
        flash('Apenas o super administrador pode excluir almoxarifados.', 'danger')
        return redirect(url_for('almoxarifados.listar'))
    
    almoxarifado = Almoxarifado.query.get_or_404(id)
    
    try:
        # Validações
        if almoxarifado.usuarios:
            flash(f'Não é possível excluir! Existem {len(almoxarifado.usuarios)} usuário(s) vinculado(s) a este almoxarifado.', 'danger')
            return redirect(url_for('almoxarifados.listar'))
        
        if almoxarifado.itens:
            flash(f'Não é possível excluir! Existem {len(almoxarifado.itens)} item(ns) cadastrado(s) neste almoxarifado.', 'danger')
            return redirect(url_for('almoxarifados.listar'))
        
        nome = almoxarifado.nome
        db.session.delete(almoxarifado)
        db.session.commit()
        
        flash(f'Almoxarifado "{nome}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir almoxarifado: {str(e)}', 'danger')
    
    return redirect(url_for('almoxarifados.listar'))
