# Como Acessar o Dashboard Online

## Opção 1: GitHub Pages (Recomendado) 🌐

### Passo a Passo:

1. **Acesse as configurações do repositório:**
   ```
   https://github.com/victorcandido1/cityexpansions_corporate/settings/pages
   ```

2. **Configure o GitHub Pages:**
   - **Source:** Selecione "Deploy from a branch"
   - **Branch:** Selecione `main`
   - **Folder:** Selecione `/ (root)` ou `/10percent` (se quiser servir apenas da pasta)
   - Clique em **Save**

3. **Aguarde alguns minutos** para o GitHub processar

4. **Acesse o dashboard:**
   ```
   https://victorcandido1.github.io/cityexpansions_corporate/
   ```
   ou
   ```
   https://victorcandido1.github.io/cityexpansions_corporate/10percent/dashboard_integrated.html
   ```

### Vantagens:
- ✅ URL permanente e profissional
- ✅ HTTPS automático
- ✅ Funciona com todos os recursos (imagens, CSS, etc.)
- ✅ Atualiza automaticamente quando você faz push

---

## Opção 2: Visualizar Diretamente no GitHub 📄

1. **Acesse o arquivo no GitHub:**
   ```
   https://github.com/victorcandido1/cityexpansions_corporate/blob/main/10percent/dashboard_integrated.html
   ```

2. **Clique em "Raw"** para ver o HTML bruto

3. **Copie a URL** e cole em um serviço como:
   - https://htmlpreview.github.io/
   - Use a extensão do navegador "HTML Preview"

### Limitações:
- ⚠️ Pode ter problemas com recursos externos
- ⚠️ Não é uma URL permanente
- ⚠️ Requer extensão ou serviço externo

---

## Opção 3: Download e Abrir Localmente 💻

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/victorcandido1/cityexpansions_corporate.git
   ```

2. **Abra o arquivo:**
   - Navegue até `10percent/dashboard_integrated.html`
   - Abra com qualquer navegador

### Vantagens:
- ✅ Funciona offline
- ✅ Todos os recursos funcionam
- ✅ Não depende de serviços externos

---

## URLs Importantes

- **Dashboard Principal:** `10percent/dashboard_integrated.html`
- **Methodology:** `10percent/METHODOLOGY.html`
- **Página Inicial:** `index.html` (se GitHub Pages configurado)

---

## Nota sobre Recursos

O dashboard referencia arquivos locais (imagens PNG, CSVs, mapas HTML). Para funcionar completamente online via GitHub Pages, você pode:

1. **Manter os arquivos no repositório** (já estão sendo ignorados pelo .gitignore)
2. **Ou usar caminhos relativos** (já configurados)
3. **Ou hospedar recursos em CDN** (opcional)

---

**Recomendação:** Use GitHub Pages (Opção 1) para a melhor experiência!

