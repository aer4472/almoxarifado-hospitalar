# 🏥 Almoxarifado Hospitalar v4.0

Sistema completo de gestão de almoxarifado hospitalar com múltiplos almoxarifados.

---

## ⚡ INSTALAÇÃO RÁPIDA

### 1️⃣ Instalar dependências
Clique duas vezes em:
```
INSTALAR_DEPENDENCIAS.bat
```

### 2️⃣ Inicializar banco de dados
Clique duas vezes em:
```
INICIAR_SISTEMA_COMPLETO.bat
```

### 3️⃣ Iniciar servidor
```
cd backend
python app.py
```

### 4️⃣ Acessar sistema
```
http://localhost:5000

Login: admin
Senha: admin123
```

---

## ✨ FUNCIONALIDADES

✅ Múltiplos almoxarifados  
✅ Controle de estoque  
✅ Entrada/Saída de materiais  
✅ Alertas de estoque mínimo  
✅ Controle de validades  
✅ Relatórios em PDF  
✅ Logo personalizado  
✅ 5 níveis de acesso  

---

## 📁 ESTRUTURA

```
almoxarifado-v4.0/
├── backend/         # Código do sistema
├── frontend/        # Templates HTML/CSS
├── database/        # Scripts do banco
└── requirements.txt # Dependências
```

---

## 👥 NÍVEIS DE ACESSO

| Nível | Descrição |
|-------|-----------|
| **Super Admin** | Controle total do sistema |
| **Admin Central** | Gerencia todos almoxarifados |
| **Admin Local** | Gerencia seu almoxarifado |
| **Colaborador** | Movimenta estoque |
| **Visualizador** | Apenas consulta |

---

## 🔧 REQUISITOS

- Python 3.8+
- Windows/Linux/Mac
- Navegador moderno

---

## 🆘 PROBLEMAS?

**Erro: "ModuleNotFoundError"**
```
pip install -r requirements.txt
```

**Erro: "no such table"**
```
INICIAR_SISTEMA_COMPLETO.bat
```

**Servidor não inicia**
```
cd backend
python app.py
```

---

## 🎯 PRIMEIRO USO

1. Login: admin / admin123
2. Cadastros → Almoxarifados → Criar
3. Gestão → Usuários → Criar
4. Cadastros → Itens → Criar
5. Movimentações → Entrada/Saída
6. Relatórios → Gerar PDF

---

**Versão:** 4.0  
**Python:** 3.8+  
**Desenvolvido com ❤️**
