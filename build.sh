#!/usr/bin/env bash
# Script de build para Render.com

set -o errexit

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Inicializar banco de dados (apenas se não existir)
if [ ! -f "almoxarifado.db" ]; then
    echo "Inicializando banco de dados..."
    python INICIAR_SISTEMA_COMPLETO.py
fi

echo "Build completo!"
