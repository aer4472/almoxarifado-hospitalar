"""
Módulo de geração de relatórios em PDF
Utiliza ReportLab para criar relatórios profissionais
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from io import BytesIO
from datetime import datetime
import os
import requests

from models import Item, Movimentacao, Configuracao, Almoxarifado


def gerar_relatorio_estoque(current_user):
    """Gera relatório de estoque atual em PDF filtrado por almoxarifado"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Buscar configurações
    config = Configuracao.query.first()
    nome_hospital = config.nome_hospital if config and config.nome_hospital else "Almoxarifado Hospitalar"
    
    # Determinar almoxarifado
    almoxarifado_nome = "Todos os Almoxarifados"
    if not current_user.ve_todos_almoxarifados and current_user.almoxarifado_id:
        almoxarifado = Almoxarifado.query.get(current_user.almoxarifado_id)
        if almoxarifado:
            almoxarifado_nome = almoxarifado.nome
    
    # Logo (se existir)
    if config and config.logo_url:
        try:
            # Tentar baixar o logo
            if config.logo_url.startswith('http'):
                response = requests.get(config.logo_url, timeout=5)
                if response.status_code == 200:
                    logo_buffer = BytesIO(response.content)
                    logo = Image(logo_buffer, width=3*cm, height=3*cm)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 10))
        except:
            pass  # Se falhar, continua sem logo
    
    # Nome do Hospital
    hospital_style = ParagraphStyle(
        'HospitalStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=5,
        alignment=1
    )
    elements.append(Paragraph(nome_hospital, hospital_style))
    
    # Nome do Almoxarifado
    almox_style = ParagraphStyle(
        'AlmoxStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#3498DB'),
        spaceAfter=20,
        alignment=1
    )
    elements.append(Paragraph(almoxarifado_nome, almox_style))
    
    # Título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=10,
        alignment=1
    )
    
    titulo = Paragraph("Relatório de Estoque", titulo_style)
    elements.append(titulo)
    
    # Data do relatório
    data_style = ParagraphStyle(
        'DataStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1
    )
    
    data_relatorio = Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
        data_style
    )
    elements.append(data_relatorio)
    elements.append(Spacer(1, 20))
    
    # Buscar itens com filtro por almoxarifado
    query = Item.query.filter_by(ativo=True)
    
    # Filtrar por almoxarifado se não for admin geral/central
    if not current_user.ve_todos_almoxarifados:
        if current_user.almoxarifado_id:
            query = query.filter_by(almoxarifado_id=current_user.almoxarifado_id)
        else:
            query = query.filter_by(almoxarifado_id=None)
    
    itens = query.order_by(Item.nome).all()
    
    # Criar tabela
    dados = [['Código', 'Nome', 'Categoria', 'Estoque', 'Un.', 'Mínimo', 'Status']]
    
    for item in itens:
        categoria = item.categoria.nome if item.categoria else '-'
        
        # Determinar status
        if item.estoque_atual <= 0:
            status = 'ZERADO'
        elif item.estoque_atual < item.estoque_minimo:
            status = 'BAIXO'
        else:
            status = 'OK'
        
        dados.append([
            item.codigo_barras or '-',
            item.nome[:30],  # Limitar tamanho
            categoria[:20],
            f'{item.estoque_atual:.2f}',
            item.unidade_medida,
            f'{item.estoque_minimo:.2f}',
            status
        ])
    
    # Estilo da tabela
    tabela = Table(dados, colWidths=[3*cm, 6*cm, 3*cm, 2*cm, 1.5*cm, 2*cm, 2*cm])
    
    tabela.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Corpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
    ]))
    
    elements.append(tabela)
    
    # Resumo
    elements.append(Spacer(1, 30))
    
    total_itens = len(itens)
    itens_baixo = sum(1 for item in itens if item.estoque_atual < item.estoque_minimo)
    itens_zerados = sum(1 for item in itens if item.estoque_atual <= 0)
    
    resumo_style = ParagraphStyle(
        'ResumoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50')
    )
    
    resumo = f"""
    <b>Resumo:</b><br/>
    Total de itens cadastrados: {total_itens}<br/>
    Itens abaixo do estoque mínimo: {itens_baixo}<br/>
    Itens com estoque zerado: {itens_zerados}
    """
    
    elements.append(Paragraph(resumo, resumo_style))
    
    # Gerar PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()


def gerar_relatorio_movimentacoes(current_user, data_inicio=None, data_fim=None):
    """Gera relatório de movimentações em PDF filtrado por almoxarifado"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    
    # Buscar configurações
    config = Configuracao.query.first()
    nome_hospital = config.nome_hospital if config and config.nome_hospital else "Almoxarifado Hospitalar"
    
    # Determinar almoxarifado
    almoxarifado_nome = "Todos os Almoxarifados"
    if not current_user.ve_todos_almoxarifados and current_user.almoxarifado_id:
        almoxarifado = Almoxarifado.query.get(current_user.almoxarifado_id)
        if almoxarifado:
            almoxarifado_nome = almoxarifado.nome
    
    # Logo (se existir)
    if config and config.logo_url:
        try:
            # Tentar baixar o logo
            if config.logo_url.startswith('http'):
                response = requests.get(config.logo_url, timeout=5)
                if response.status_code == 200:
                    logo_buffer = BytesIO(response.content)
                    logo = Image(logo_buffer, width=3*cm, height=3*cm)
                    logo.hAlign = 'CENTER'
                    elements.append(logo)
                    elements.append(Spacer(1, 10))
        except:
            pass  # Se falhar, continua sem logo
    
    # Nome do Hospital
    hospital_style = ParagraphStyle(
        'HospitalStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=5,
        alignment=1
    )
    elements.append(Paragraph(nome_hospital, hospital_style))
    
    # Nome do Almoxarifado
    almox_style = ParagraphStyle(
        'AlmoxStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#3498DB'),
        spaceAfter=20,
        alignment=1
    )
    elements.append(Paragraph(almoxarifado_nome, almox_style))
    
    # Título
    titulo_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2C3E50'),
        spaceAfter=10,
        alignment=1
    )
    
    titulo = Paragraph("Relatório de Movimentações", titulo_style)
    elements.append(titulo)
    
    # Data do relatório
    data_style = ParagraphStyle(
        'DataStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        alignment=1
    )
    
    periodo = ""
    if data_inicio and data_fim:
        periodo = f"<br/>Período: {data_inicio} a {data_fim}"
    
    data_relatorio = Paragraph(
        f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}{periodo}",
        data_style
    )
    elements.append(data_relatorio)
    elements.append(Spacer(1, 20))
    
    # Buscar movimentações com filtro
    query = Movimentacao.query
    
    # Filtrar por data
    if data_inicio and data_fim:
        data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d')
        data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d')
        query = query.filter(Movimentacao.data_hora.between(data_inicio_obj, data_fim_obj))
    
    # Filtrar por almoxarifado se não for admin geral/central
    if not current_user.ve_todos_almoxarifados and current_user.almoxarifado_id:
        # Pegar IDs dos itens do almoxarifado do usuário
        itens_almoxarifado = Item.query.filter_by(
            almoxarifado_id=current_user.almoxarifado_id
        ).all()
        itens_ids = [item.id for item in itens_almoxarifado]
        
        # Filtrar movimentações desses itens
        if itens_ids:
            query = query.filter(Movimentacao.item_id.in_(itens_ids))
        else:
            # Sem itens, sem movimentações
            query = query.filter(Movimentacao.id == None)
    
    movimentacoes = query.order_by(Movimentacao.data_hora.desc()).limit(100).all()
    
    # Criar tabela
    dados = [['Data/Hora', 'Tipo', 'Item', 'Qtd', 'Setor', 'Usuário']]
    
    for mov in movimentacoes:
        tipo = mov.tipo.upper()
        setor = mov.setor.nome if mov.setor else '-'
        
        dados.append([
            mov.data_hora.strftime('%d/%m/%Y %H:%M'),
            tipo,
            mov.item.nome[:25],
            f'{mov.quantidade:.2f}',
            setor[:15],
            mov.usuario.nome[:15]
        ])
    
    # Estilo da tabela
    tabela = Table(dados, colWidths=[3.5*cm, 2*cm, 5.5*cm, 2*cm, 3*cm, 3*cm])
    
    tabela.setStyle(TableStyle([
        # Cabeçalho
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Corpo
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
    ]))
    
    elements.append(tabela)
    
    # Resumo
    elements.append(Spacer(1, 30))
    
    total_mov = len(movimentacoes)
    entradas = sum(1 for m in movimentacoes if m.tipo == 'entrada')
    saidas = sum(1 for m in movimentacoes if m.tipo == 'saida')
    ajustes = sum(1 for m in movimentacoes if m.tipo == 'ajuste')
    
    resumo_style = ParagraphStyle(
        'ResumoStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2C3E50')
    )
    
    resumo = f"""
    <b>Resumo:</b><br/>
    Total de movimentações: {total_mov}<br/>
    Entradas: {entradas}<br/>
    Saídas: {saidas}<br/>
    Ajustes: {ajustes}
    """
    
    elements.append(Paragraph(resumo, resumo_style))
    
    # Gerar PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.getvalue()
