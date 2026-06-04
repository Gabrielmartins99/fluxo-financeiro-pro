import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import json
import requests
from supabase import create_client, Client
import google.generativeai as genai
import extra_streamlit_components as stx
import streamlit.components.v1 as components

# ========================================================
# 1. CREDENCIAIS BASE
# ========================================================
SUPABASE_URL = "https://tlrrauzylknuatajzniu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRscnJhdXp5bGtudWF0YWp6bml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1MDE5ODMsImV4cCI6MjA5NjA3Nzk4M30.WiTNExA0hJY0AmDY794F7O0ft2SngctNoWQ_LBwyGDk"

try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except:
    GEMINI_API_KEY = ""

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

if GEMINI_API_KEY and GEMINI_API_KEY.strip() != "":
    genai.configure(api_key=GEMINI_API_KEY)
    modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
else:
    modelo_ia = None

# ========================================================
# 2. CONFIGURAÇÃO VISUAL
# ========================================================
st.set_page_config(page_title="Fluxo Financeiro PRO", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { font-family: 'Plus Jakarta Sans', sans-serif !important; background-color: #F8FAFC !important; color: #0F172A !important; }
        h1, h2, h3 { font-weight: 800 !important; letter-spacing: -1px !important; color: #0F172A !important; }
        .title-gradient { background: linear-gradient(90deg, #0284C7 0%, #4F46E5 50%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding-bottom: 10px; }
        div[data-baseweb="input"], .stSelectbox div { border-radius: 10px !important; }
        div.stButton > button[kind="primary"] { background: linear-gradient(90deg, #0284C7 0%, #4F46E5 100%) !important; border: none !important; color: white !important; font-weight: bold; border-radius: 10px; }
        .executive-box { background-color: #FFFFFF; border: 1px solid rgba(15,23,42,0.06); border-radius: 16px; padding: 20px; box-shadow: 0 10px 30px rgba(15,23,42,0.04); }
        .status-box { padding: 20px; border-radius: 10px; background-color: #ECFDF5; border: 1px solid #10B981; color: #065F46; font-weight: bold; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. AUTENTICAÇÃO E VARIÁVEIS DE SESSÃO
# ========================================================
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "orcamentos" not in st.session_state:
    st.session_state.orcamentos = {}

cookie_manager = stx.CookieManager(key="meu_gerenciador_cookies")

if st.session_state.user_email is None:
    cookie_email = cookie_manager.get(cookie="user_email")
    if cookie_email: st.session_state.user_email = cookie_email

if not st.session_state.user_email:
    st.markdown("<h1 class='title-gradient' style='text-align: center; margin-top: 50px;'>Fluxo Financeiro PRO</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container(border=True):
            aba_login, aba_registro = st.tabs(["🔒 Entrar", "✨ Criar Conta"])
            with aba_login:
                email_login = st.text_input("E-mail corporativo ou pessoal", key="log_email")
                senha_login = st.text_input("Senha de acesso", type="password", key="log_senha")
                if st.button("Acessar Painel", type="primary", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email_login, "password": senha_login})
                        st.session_state.user_email = res.user.email
                        cookie_manager.set("user_email", res.user.email, max_age=30*24*60*60)
                        st.rerun()
                    except: st.error("E-mail ou senha incorretos.")
            with aba_registro:
                email_reg = st.text_input("Melhor E-mail", key="reg_email")
                senha_reg = st.text_input("Crie uma Senha Forte", type="password", key="reg_senha")
                if st.button("Garantir Meu Acesso", type="primary", use_container_width=True):
                    try:
                        supabase.auth.sign_up({"email": email_reg, "password": senha_reg})
                        st.success("✅ Conta criada com sucesso! Faça login ao lado.")
                    except: st.error("Erro ao criar conta.")
    st.stop()

# ========================================================
# 4. FUNÇÕES BASE E LISTAS INTELIGENTES
# ========================================================
def carregar_dados():
    try:
        response = supabase.table("lancamentos").select("*").eq("user_email", st.session_state.user_email).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Garantir que a coluna 'id' seja mapeada corretamente
            df = df.rename(columns={"id": "ID", "data_compra": "Data", "competencia": "Competencia", "tipo": "Tipo", "categoria": "Categoria", "subcategoria": "Subcategoria", "conta_cartao": "Conta_Cartao", "valor": "Valor", "descricao": "Descricao", "parcela": "Parcela", "responsavel": "Responsavel", "status": "Status"})
            df["Valor"] = pd.to_numeric(df["Valor"]).fillna(0.0)
            return df
    except: pass
    return pd.DataFrame(columns=["ID", "Data", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status"])

df = carregar_dados()

def obter_opcoes(coluna, lista_base):
    if not df.empty and coluna in df.columns:
        existentes = df[coluna].dropna().astype(str).unique().tolist()
        lista_completa = list(set(lista_base + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]]))
        return sorted(lista_completa)
    return sorted(lista_base)

LISTA_BANCOS = ["Nubank", "Inter", "Itaú", "Bradesco", "Banco do Brasil", "Pix/Dinheiro"]
LISTA_CATEGORIAS = ["Alimentação", "Transporte", "Moradia", "Salário", "Lazer", "Saúde", "Educação", "Investimentos", "Outros"]

# ========================================================
# 5. HEADER
# ========================================================
c_head1, c_head2 = st.columns([4, 1])
with c_head1: st.markdown("<h2 class='title-gradient'>Fluxo Financeiro PRO</h2>", unsafe_allow_html=True)
with c_head2:
    st.write(f"👤 {st.session_state.user_email.split('@')[0]}")
    if st.button("Sair (Logout)"):
        cookie_manager.delete("user_email")
        st.session_state.user_email = None
        st.rerun()

aba_dashboard, aba_lancamentos, aba_assistente, aba_openfinance = st.tabs(["📊 Dashboard", "📝 Lançamentos", "🤖 Assistente IA", "🔌 Open Finance"])

# ========================================================
# 6. DASHBOARD
# ========================================================
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        dash_mensal, dash_anual, dash_metas = st.tabs(["📅 Visão Mensal", "📈 Visão Anual", "🎯 Metas e Orçamentos"])
        
        with dash_mensal:
            col_filtro1, _ = st.columns(2)
            with col_filtro1:
                mes_selecionado = st.selectbox("Selecione o Mês", ["Ver Tudo"] + sorted(df["Competencia"].unique(), reverse=True))
            
            df_dash = df[df["Competencia"] == mes_selecionado] if mes_selecionado != "Ver Tudo" else df.copy()
            
            t_rec = df_dash[df_dash["Tipo"] == "Receita"]["Valor"].sum()
            t_desp = df_dash[df_dash["Tipo"] == "Despesa"]["Valor"].sum()
            t_inv = df_dash[df_dash["Tipo"] == "Investimento"]["Valor"].sum()
            saldo_liquido = t_rec - t_desp - t_inv
            
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f'<div class="executive-box" style="border-top: 4px solid #0284C7;"><div class="term-label">Saldo Conta (Sobra)</div><div class="term-amount" style="color:#0284C7;">R$ {saldo_liquido:,.2f}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="executive-box" style="border-top: 4px solid #16A34A;"><div class="term-label">Entradas (+)</div><div class="term-amount" style="color:#16A34A;">R$ {t_rec:,.2f}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="executive-box" style="border-top: 4px solid #DC2626;"><div class="term-label">Despesas (-)</div><div class="term-amount" style="color:#DC2626;">R$ {t_desp:,.2f}</div></div>', unsafe_allow_html=True)
            c4.markdown(f'<div class="executive-box" style="border-top: 4px solid #8B5CF6;"><div class="term-label">Investido (💼)</div><div class="term-amount" style="color:#8B5CF6;">R$ {t_inv:,.2f}</div></div>', unsafe_allow_html=True)
            
            if t_desp > 0:
                st.markdown("<br>", unsafe_allow_html=True)
                col_graf1, col_graf2 = st.columns(2)
                with col_graf1: st.plotly_chart(px.pie(df_dash[df_dash["Tipo"] == "Despesa"], values="Valor", names="Categoria", title="Distribuição de Despesas"), use_container_width=True)
                with col_graf2: st.plotly_chart(px.bar(df_dash[df_dash["Tipo"] == "Despesa"].groupby("Descricao")["Valor"].sum().reset_index().sort_values("Valor", ascending=False).head(5), x="Valor", y="Descricao", orientation='h', title="Top 5 Maiores Gastos"), use_container_width=True)
        
        with dash_anual:
            st.plotly_chart(px.bar(df.groupby(["Competencia", "Tipo"])["Valor"].sum().reset_index(), x="Competencia", y="Valor", color="Tipo", barmode="group", title="Evolução Mensal (Receitas vs Despesas vs Investimentos)", color_discrete_map={"Receita": "#16A34A", "Despesa": "#DC2626", "Investimento": "#8B5CF6"}), use_container_width=True)
            
        with dash_metas:
            st.markdown("### Controle de Gastos por Categoria")
            c_meta1, c_meta2 = st.columns([1, 2])
            with c_meta1:
                with st.container(border=True):
                    st.markdown("#### Nova Meta")
                    cat_meta = st.selectbox("Escolha a Categoria", obter_opcoes("Categoria", LISTA_CATEGORIAS))
                    limite_meta = st.number_input("Limite Máximo (R$)", min_value=0.0, value=500.0, step=50.0)
                    if st.button("Salvar Meta", type="primary", use_container_width=True):
                        st.session_state.orcamentos[cat_meta] = limite_meta
                        st.success(f"Meta para {cat_meta} registrada!")
                        time.sleep(1)
                        st.rerun()
            with c_meta2:
                mes_atual_metas = datetime.now().strftime("%Y-%m")
                st.markdown(f"#### Termômetro do Mês ({mes_atual_metas})")
                df_mes_metas = df[(df["Competencia"] == mes_atual_metas) & (df["Tipo"] == "Despesa")]
                if not st.session_state.orcamentos:
                    st.info("💡 Você ainda não possui metas definidas. Crie uma meta ao lado.")
                else:
                    for cat, limite in st.session_state.orcamentos.items():
                        gasto_atual = df_mes_metas[df_mes_metas["Categoria"] == cat]["Valor"].sum()
                        percentual = min(gasto_atual / limite, 1.0) if limite > 0 else 1.0 if gasto_atual > 0 else 0.0
                        st.write(f"**{cat}**: R$ {gasto_atual:,.2f} de R$ {limite:,.2f}")
                        st.progress(percentual)
                        if percentual >= 1.0: st.error("🚨 Orçamento estourado nesta categoria!")
                        elif percentual >= 0.8: st.warning("⚠️ Atenção! Perto do limite.")
                        st.markdown("---")
    else: st.info("O Dashboard aguarda lançamentos.")

# ========================================================
# 7. LANÇAMENTOS (INCLUI EDIÇÃO E EXCLUSÃO)
# ========================================================
with aba_lancamentos:
    aba_manual, aba_importar, aba_gerenciar = st.tabs(["✍️ Novo Lançamento", "📥 Importar Fatura", "✏️ Gerenciar (Editar/Apagar)"])
    
    with aba_manual:
        st.subheader("Registrar Movimentação")
        st.write("Dica: Selecione '➕ Novo(a)...' nas listas abaixo para adicionar seus próprios nomes.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo = st.selectbox("Tipo", ["Despesa", "Receita", "Investimento"])
            data_compra = st.date_input("Data do Ocorrido")
            valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
            st.markdown("---")
            modo_lancamento = st.radio("Frequência:", ["Único (À vista)", "Parcelado", "Assinatura Mensal"])
            
        with col2:
            opcoes_cat = obter_opcoes("Categoria", LISTA_CATEGORIAS) + ["➕ Nova Categoria..."]
            cat_sel = st.selectbox("Categoria", opcoes_cat)
            categoria = st.text_input("Digite a Nova Categoria:") if cat_sel == "➕ Nova Categoria..." else cat_sel

            opcoes_conta = obter_opcoes("Conta_Cartao", LISTA_BANCOS) + ["➕ Nova Conta..."]
            conta_sel = st.selectbox("Conta / Cartão", opcoes_conta)
            conta_cartao = st.text_input("Digite a Nova Conta:") if conta_sel == "➕ Nova Conta..." else conta_sel

            descricao = st.text_input("Descrição")
            st.markdown("---")
            
            if modo_lancamento == "Parcelado": parcelas = st.number_input("Parcelas", min_value=2, max_value=120, value=2)
            elif modo_lancamento == "Assinatura Mensal": parcelas = st.number_input("Projetar Meses", min_value=2, max_value=60, value=12)
            else: parcelas = 1

        with col3:
            opcoes_resp = obter_opcoes("Responsavel", ["Gabriel", "Tainá", "Família", "Empresa"]) + ["➕ Novo Responsável..."]
            resp_sel = st.selectbox("Responsável", opcoes_resp)
            responsavel = st.text_input("Digite o Novo Responsável:") if resp_sel == "➕ Novo Responsável..." else resp_sel

            mes_fatura = st.date_input("Mês da Competência")

        if st.button("💾 Gravar no Sistema", type="primary", use_container_width=True):
            if valor_total > 0 and categoria and conta_cartao and responsavel:
                novas_linhas = []
                valor_por_mes = valor_total / parcelas if modo_lancamento == "Parcelado" else valor_total
                for i in range(parcelas):
                    m = mes_fatura.month - 1 + i
                    comp = f"{mes_fatura.year + (m // 12)}-{(m % 12) + 1:02d}"
                    novas_linhas.append({"user_email": st.session_state.user_email, "data_compra": data_compra.strftime("%Y-%m-%d"), "competencia": comp, "tipo": tipo, "categoria": categoria, "subcategoria": "Geral", "conta_cartao": conta_cartao, "valor": float(round(valor_por_mes, 2)), "descricao": descricao, "parcela": f"{i+1}/{parcelas}" if modo_lancamento == "Parcelado" else "Recorrente" if modo_lancamento == "Assinatura Mensal" else "À vista", "responsavel": responsavel, "status": "Pago" if i == 0 else "Pendente"})
                supabase.table("lancamentos").insert(novas_linhas).execute()
                st.success("✅ Lançamento salvo!")
                time.sleep(1)
                st.rerun()
            else: st.warning("Preencha todos os dados.")

    with aba_importar:
        st.subheader("Integração Inteligente de Faturas")
        arquivo = st.file_uploader("Anexe sua fatura CSV/Excel", type=["csv", "xlsx", "xls"])
        if arquivo:
            df_fatura = pd.read_csv(arquivo, sep=None, engine='python') if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
            df_fatura["Categoria_Sistema"] = "Outros"
            df_fatura["Tipo_Sistema"] = "Despesa"
            c1, c2, c3 = st.columns(3)
            col_data = c1.selectbox("Coluna Data?", df_fatura.columns)
            col_desc = c2.selectbox("Coluna Descrição?", df_fatura.columns)
            col_valor = c3.selectbox("Coluna Valor?", df_fatura.columns)
            df_editado = st.data_editor(df_fatura, num_rows="dynamic", use_container_width=True)
            if st.button("🚀 Salvar Lançamentos", type="primary"):
                novas_linhas = []
                for index, row in df_editado.iterrows():
                    try: val = float(str(row[col_valor]).replace('R$', '').replace('.', '').replace(',', '.').strip())
                    except: val = 0.0
                    if val != 0: novas_linhas.append({"user_email": st.session_state.user_email, "data_compra": str(row[col_data])[:10], "competencia": datetime.now().strftime("%Y-%m"), "tipo": row.get("Tipo_Sistema", "Despesa"), "categoria": row.get("Categoria_Sistema", "Outros"), "conta_cartao": "Importado", "valor": abs(val), "descricao": str(row[col_desc]), "parcela": "Fatura", "responsavel": "Eu", "status": "Pago"})
                if novas_linhas:
                    supabase.table("lancamentos").insert(novas_linhas).execute()
                    st.success("Importado!")
                    time.sleep(1)
                    st.rerun()

    # O NOVO MÓDULO DE EDIÇÃO!
    with aba_gerenciar:
        st.subheader("Gerenciar Movimentações")
        if df.empty:
            st.info("Você ainda não tem lançamentos salvos no banco de dados.")
        else:
            # Tabela Visual para ajudar a achar o registro
            st.dataframe(df[["Data", "Competencia", "Tipo", "Categoria", "Conta_Cartao", "Descricao", "Valor"]].sort_values("Data", ascending=False), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.write("### 🛠️ Editar ou Excluir um Registro")
            
            # Cria a lista de opções formatadas bonitinhas
            opcoes_edit = {row["ID"]: f"{row['Data']} | {row['Descricao']} | R$ {row['Valor']:.2f}" for idx, row in df.iterrows()}
            id_selecionado = st.selectbox("Selecione o Lançamento que deseja alterar:", options=list(opcoes_edit.keys()), format_func=lambda x: opcoes_edit[x])
            
            if id_selecionado:
                linha_edit = df[df["ID"] == id_selecionado].iloc[0]
                
                c_ed1, c_ed2, c_ed3 = st.columns(3)
                with c_ed1:
                    novo_tipo = st.selectbox("Tipo", ["Despesa", "Receita", "Investimento"], index=["Despesa", "Receita", "Investimento"].index(linha_edit["Tipo"]) if linha_edit["Tipo"] in ["Despesa", "Receita", "Investimento"] else 0, key="ed_tipo")
                    try: data_atual = pd.to_datetime(linha_edit["Data"])
                    except: data_atual = datetime.now()
                    nova_data = st.date_input("Data", data_atual, key="ed_data")
                    novo_valor = st.number_input("Valor (R$)", value=float(linha_edit["Valor"]), min_value=0.0, key="ed_valor")
                with c_ed2:
                    nova_cat = st.text_input("Categoria", value=str(linha_edit["Categoria"]), key="ed_cat")
                    nova_conta = st.text_input("Conta / Cartão", value=str(linha_edit["Conta_Cartao"]), key="ed_conta")
                    nova_desc = st.text_input("Descrição", value=str(linha_edit["Descricao"]), key="ed_desc")
                with c_ed3:
                    novo_resp = st.text_input("Responsável", value=str(linha_edit["Responsavel"]), key="ed_resp")
                    nova_comp = st.text_input("Competência (YYYY-MM)", value=str(linha_edit["Competencia"]), key="ed_comp")
                
                st.markdown("<br>", unsafe_allow_html=True)
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
                        try:
                            supabase.table("lancamentos").update({"tipo": novo_tipo, "data_compra": nova_data.strftime("%Y-%m-%d"), "valor": novo_valor, "categoria": nova_cat, "conta_cartao": nova_conta, "descricao": nova_desc, "responsavel": novo_resp, "competencia": nova_comp}).eq("id", id_selecionado).execute()
                            st.success("✅ Atualizado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao atualizar: {e}")
                with c_btn2:
                    if st.button("🗑️ Apagar Registro", use_container_width=True):
                        try:
                            supabase.table("lancamentos").delete().eq("id", id_selecionado).execute()
                            st.error("🗑️ Registro apagado para sempre!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Erro ao apagar: {e}")

# ========================================================
# 8. ASSISTENTE IA
# ========================================================
with aba_assistente:
    st.markdown("### 🤖 Cérebro Digital")
    if modelo_ia:
        if "mensagens_chat" not in st.session_state: st.session_state.mensagens_chat = [{"role": "assistant", "content": "Olá! Me peça para registrar um gasto!"}]
        for msg in st.session_state.mensagens_chat:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])
        prompt = st.chat_input("Digite sua mensagem...")
        if prompt:
            st.session_state.mensagens_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.markdown(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Processando..."):
                    try:
                        resposta = modelo_ia.generate_content(f'O usuário disse: "{prompt}". Se for um gasto, gere um JSON no final com acao: registrar, tipo, valor, descricao, categoria, conta.')
                        texto_resposta = resposta.text
                        st.markdown(texto_resposta.split("```json")[0].strip())
                        st.session_state.mensagens_chat.append({"role": "assistant", "content": texto_resposta.split("```json")[0].strip()})
                        if "```json" in texto_resposta:
                            dados_ia = json.loads(texto_resposta.split("```json")[1].split("```")[0].strip())
                            if dados_ia.get("acao") == "registrar":
                                supabase.table("lancamentos").insert({"user_email": st.session_state.user_email, "data_compra": datetime.now().strftime("%Y-%m-%d"), "competencia": datetime.now().strftime("%Y-%m"), "tipo": dados_ia.get("tipo", "Despesa"), "categoria": dados_ia.get("categoria", "Outros"), "conta_cartao": dados_ia.get("conta", "IA"), "valor": float(dados_ia.get("valor", 0.0)), "descricao": dados_ia.get("descricao", "Assistente"), "parcela": "À vista", "responsavel": "Eu", "status": "Pago"}).execute()
                                st.toast("✅ Registrado pela IA!")
                    except: st.error("Erro de IA.")

# ========================================================
# 9. OPEN FINANCE
# ========================================================
with aba_openfinance:
    st.subheader("🔌 Hub de Integração Bancária")
    if "banco_conectado" not in st.session_state: st.session_state.banco_conectado = False

    if not st.session_state.banco_conectado:
        st.write("Clique abaixo para simular uma conexão bem-sucedida e destravar as próximas funcionalidades.")
        if st.button("🚀 Simular Conexão (Bypass)", type="primary"):
            with st.spinner("Simulando comunicação criptografada..."):
                time.sleep(1)
                st.session_state.banco_conectado = True
                st.session_state.item_id_simulado = f"item_sandbox_{int(time.time())}"
                st.rerun()
    else:
        st.markdown(f"<div class='status-box'>🎉 MÁGICA CONCLUÍDA!<br><br>O banco foi conectado com sucesso via API.<br>Item ID: {st.session_state.item_id_simulado}</div>", unsafe_allow_html=True)
        st.write("")
        if st.button("🔴 Desconectar Conta"):
            st.session_state.banco_conectado = False
            st.rerun()
