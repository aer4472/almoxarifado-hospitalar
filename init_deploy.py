"""Inicialização automática para deploy"""
import os
import sys

backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_path)

from database.init_db import inicializar_banco

def main():
    print("Inicializando banco de dados...")
    try:
        inicializar_banco()
        print("✓ Banco inicializado!")
        print("Login: admin / admin123")
        return 0
    except Exception as e:
        print(f"✗ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())