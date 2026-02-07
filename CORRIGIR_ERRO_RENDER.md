# 🚨 CORRIGIR ERRO "Exited with status 1" NO RENDER

## ❌ ERRO QUE VOCÊ ESTÁ VENDO:

```
Exited with status 1 while running your code.
```

**Causa:** Faltam arquivos de configuração para o Render.

---

## ✅ SOLUÇÃO EM 5 PASSOS (10 MINUTOS):

### **PASSO 1: Adicionar gunicorn no requirements.txt**

No seu repositório GitHub, edite o arquivo `requirements.txt`:

1. Abra o arquivo `requirements.txt`
2. Clique no ícone de lápis (Edit)
3. **Adicione esta linha no final:**
   ```
   gunicorn==21.2.0
   ```

4. O arquivo completo deve ficar assim:
   ```
   Flask==3.0.0
   Flask-SQLAlchemy==3.1.1
   Flask-Login==0.6.3
   Werkzeug==3.0.1
   reportlab==4.0.7
   python-dotenv==1.0.0
   requests==2.31.0
   gunicorn==21.2.0
   ```

5. Clique em: "Commit changes"

---

### **PASSO 2: Criar arquivo build.sh**

No GitHub, na raiz do projeto:

1. Clique em: "Add file" → "Create new file"
2. Nome do arquivo: `build.sh`
3. Cole este conteúdo:

```bash
#!/usr/bin/env bash
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f "almoxarifado.db" ]; then
    echo "Inicializando banco de dados..."
    python INICIAR_SISTEMA_COMPLETO.py
fi

echo "Build completo!"
```

4. Clique em: "Commit new file"

---

### **PASSO 3: Verificar estrutura do projeto**

Certifique-se que no GitHub você tem:

```
almoxarifado-hospitalar/
├── backend/
│   ├── app.py          ← IMPORTANTE!
│   ├── models.py
│   └── ...
├── frontend/
├── database/
├── requirements.txt    ← Deve ter gunicorn
├── build.sh           ← Novo arquivo
├── INICIAR_SISTEMA_COMPLETO.py
└── .env
```

---

### **PASSO 4: Configurar no Render**

1. Volte para o Render Dashboard
2. Encontre seu serviço (almoxarifado-hospitalar)
3. Clique em "Settings"

**Build Command:**
```
./build.sh
```

**Start Command:**
```
cd backend && gunicorn --bind 0.0.0.0:$PORT app:app
```

**Environment:**
- Python 3

4. Clique em: "Save Changes"

---

### **PASSO 5: Fazer novo deploy**

1. No Render, clique em: "Manual Deploy"
2. Escolha: "Deploy latest commit"
3. Aguarde 2-5 minutos
4. Veja os logs aparecerem

**Deve aparecer:**
```
==> Building...
Installing dependencies...
✓ Flask installed
✓ gunicorn installed
Inicializando banco de dados...
✓ Banco criado!
Build completo!

==> Starting...
[gunicorn] Starting gunicorn
[gunicorn] Listening at: 0.0.0.0:10000
✓ Deploy successful!
```

---

## 🎯 ALTERNATIVA MAIS SIMPLES:

Se o erro persistir, use esta configuração MINIMALISTA:

### **No Render Dashboard → Settings:**

**Build Command:**
```
pip install -r requirements.txt && python INICIAR_SISTEMA_COMPLETO.py
```

**Start Command:**
```
cd backend && python app.py
```

**Salve e faça novo deploy manual.**

---

## 🆘 AINDA COM ERRO?

### **Ver logs completos:**

1. No Render, clique no seu serviço
2. Aba "Logs"
3. Veja as últimas mensagens

**Erros comuns e soluções:**

```
ModuleNotFoundError: No module named 'gunicorn'
→ Adicione gunicorn no requirements.txt

bash: ./build.sh: Permission denied
→ No GitHub: git update-index --chmod=+x build.sh

ImportError: cannot import name 'app'
→ Verifique se backend/app.py existe

Port already in use
→ Use: gunicorn --bind 0.0.0.0:$PORT app:app
```

---

## 📋 CHECKLIST ANTES DE DEPLOY:

- [ ] `requirements.txt` tem gunicorn==21.2.0
- [ ] Arquivo `build.sh` existe na raiz
- [ ] Pasta `backend/` tem `app.py`
- [ ] `INICIAR_SISTEMA_COMPLETO.py` existe na raiz
- [ ] Build Command: `./build.sh`
- [ ] Start Command: `cd backend && gunicorn --bind 0.0.0.0:$PORT app:app`
- [ ] Cliquei em "Manual Deploy"

---

## 🎯 SOLUÇÃO GARANTIDA:

Se NADA funcionar, faça isto:

### **1. Delete o serviço no Render**
### **2. Crie novo serviço com estas configurações EXATAS:**

**Repositório:** seu-usuario/almoxarifado-hospitalar

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
python INICIAR_SISTEMA_COMPLETO.py && cd backend && python app.py
```

**Environment Variables:**
- Nome: `PORT`
- Valor: `10000`

**Clique em: "Create Web Service"**

---

## 💡 DICA PRO:

O Render prefere que você:
1. Tenha um Procfile OU
2. Configure os comandos manualmente

**Crie arquivo `Procfile` na raiz:**
```
web: cd backend && gunicorn app:app
```

E deixe os comandos em branco no Render.

---

## ✅ QUANDO FUNCIONAR:

Você verá:
```
Your service is live at:
https://almoxarifado-hospitalar-xxxx.onrender.com

✓ Deploy successful
```

**Acesse a URL e verá a tela de login!**

**Login:** admin  
**Senha:** admin123

---

**Tente essas soluções e me diga qual erro aparece nos logs!** 🚀
