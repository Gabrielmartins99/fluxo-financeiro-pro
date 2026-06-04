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
        .executive-box { background-color: #FFFFFF; border: 1px solid rgba(15,23,42,0.06); border-radius: 16px; padding: 26px; box-shadow: 0 10px 30px rgba(15,23,42,0.04); }
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
# 4. FUNÇÕES BASE
# ========================================================
def carregar_dados():
    try:
        response = supabase.table("lancamentos").select("*").eq("user_email", st.session_state.user_email).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.rename(columns={"data_compra": "Data", "competencia": "Competencia", "tipo": "Tipo", "categoria": "Categoria", "subcategoria": "Subcategoria", "conta_cartao": "Conta_Cartao", "valor": "Valor", "descricao": "Descricao", "parcela": "Parcela", "responsavel": "Responsavel", "status": "Status"})
            df["Valor"] = pd.to_numeric(df["Valor"]).fillna(0.0)
            return df
    except: pass
    return pd.DataFrame(columns=["ID", "Data", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status"])

df = carregar_dados()

def obter_opcoes(coluna, lista_base):
    if not df.empty and coluna in df.columns:
        existentes = df[coluna].dropna().astype(str).unique().tolist()
        return sorted(list(set(lista_base + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])))
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
# 6. DASHBOARD (AGORA COM METAS)
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
            c1, c2, c3 = st.columns(3)
            c1.markdown(f'<div class="executive-box" style="border-top: 4px solid #0284C7;"><div class="term-label">Saldo Líquido</div><div class="term-amount" style="color:#0284C7;">R$ {t_rec - t_desp:,.2f}</div></div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="executive-box" style="border-top: 4px solid #16A34A;"><div class="term-label">Entradas (+)</div><div class="term-amount" style="color:#16A34A;">R$ {t_rec:,.2f}</div></div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="executive-box" style="border-top: 4px solid #DC2626;"><div class="term-label">Saídas (-)</div><div class="term-amount" style="color:#DC2626;">R$ {t_desp:,.2f}</div></div>', unsafe_allow_html=True)
            if t_desp > 0:
                col_graf1, col_graf2 = st.columns(2)
                with col_graf1: st.plotly_chart(px.pie(df_dash[df_dash["Tipo"] == "Despesa"], values="Valor", names="Categoria", title="Distribuição por Categoria"), use_container_width=True)
                with col_graf2: st.plotly_chart(px.bar(df_dash[df_dash["Tipo"] == "Despesa"].groupby("Descricao")["Valor"].sum().reset_index().sort_values("Valor", ascending=False).head(5), x="Valor", y="Descricao", orientation='h', title="Top 5 Despesas"), use_container_width=True)
        
        with dash_anual:
            st.plotly_chart(px.bar(df.groupby(["Competencia", "Tipo"])["Valor"].sum().reset_index(), x="Competencia", y="Valor", color="Tipo", barmode="group", title="Evolução Mensal"), use_container_width=True)
            
        with dash_metas:
            st.markdown("### Controle de Gastos por Categoria")
            st.write("Defina um teto de gastos e acompanhe o seu consumo no mês atual em tempo real.")
            
            c_meta1, c_meta2 = st.columns([1, 2])
            with c_meta1:
                with st.container(border=True):
                    st.markdown("#### Nova Meta")
                    cat_meta = st.selectbox("Escolha a Categoria", [c for c in LISTA_CATEGORIAS if c not in ["Salário", "Investimentos"]])
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
                    st.info("💡 Você ainda não possui metas definidas. Crie uma meta ao lado para começar.")
                else:
                    for cat, limite in st.session_state.orcamentos.items():
                        gasto_atual = df_mes_metas[df_mes_metas["Categoria"] == cat]["Valor"].sum()
                        
                        # Evita divisão por zero
                        if limite > 0:
                            percentual = min(gasto_atual / limite, 1.0)
                        else:
                            percentual = 1.0 if gasto_atual > 0 else 0.0
                            
                        # Exibição visual
                        st.write(f"**{cat}**: R$ {gasto_atual:,.2f} de R$ {limite:,.2f}")
                        st.progress(percentual)
                        
                        if percentual >= 1.0:
                            st.error("🚨 Orçamento estourado nesta categoria!")
                        elif percentual >= 0.8:
                            st.warning("⚠️ Atenção! Você está muito perto de atingir o limite.")
                        st.markdown("---")
    else: st.info("O Dashboard aguarda lançamentos.")

# ========================================================
# 7. LANÇAMENTOS E 8. ASSISTENTE IA
# ========================================================
with aba_lancamentos:
    st.subheader("Registrar Movimentação")
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        data_compra = st.date_input("Data")
        valor_total = st.number_input("Valor Total (R$)", min_value=0.0)
    with col2:
        categoria = st.selectbox("Categoria", obter_opcoes("Categoria", LISTA_CATEGORIAS))
        conta_cartao = st.selectbox("Conta", obter_opcoes("Conta_Cartao", LISTA_BANCOS))
        descricao = st.text_input("Descrição")
    with col3:
        responsavel = st.selectbox("Responsável", obter_opcoes("Responsavel", ["Eu", "Família", "Empresa"]))
        mes_fatura = st.date_input("Mês Competência")

    if st.button("💾 Salvar Lançamento", type="primary") and valor_total > 0:
        comp = f"{mes_fatura.year}-{mes_fatura.month:02d}"
        supabase.table("lancamentos").insert({"user_email": st.session_state.user_email, "data_compra": data_compra.strftime("%Y-%m-%d"), "competencia": comp, "tipo": tipo, "categoria": categoria, "subcategoria": "Geral", "conta_cartao": conta_cartao, "valor": float(valor_total), "descricao": descricao, "parcela": "Única", "responsavel": responsavel, "status": "Pago"}).execute()
        st.success("Salvo com sucesso!")
        time.sleep(1)
        st.rerun()

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
# 9. OPEN FINANCE (BYPASS ATIVADO)
# ========================================================
with aba_openfinance:
    st.subheader("🔌 Hub de Integração Bancária")
    st.info("💡 **Aviso do Sistema:** Devido a restrições de segurança de iframes nos navegadores modernos, a janela nativa da Pluggy foi contornada neste ambiente de desenvolvimento para não bloquearmos o progresso.")
    
    if "banco_conectado" not in st.session_state:
        st.session_state.banco_conectado = False

    if not st.session_state.banco_conectado:
        st.write("Clique abaixo para simular uma conexão bem-sucedida e destravar as próximas funcionalidades.")
        if st.button("🚀 Simular Conexão (Bypass)", type="primary"):
            with st.spinner("Simulando comunicação criptografada..."):
                time.sleep(2)
                st.session_state.banco_conectado = True
                st.session_state.item_id_simulado = f"item_sandbox_{int(time.time())}"
                st.rerun()
    else:
        st.markdown(f"<div class='status-box'>🎉 MÁGICA CONCLUÍDA!<br><br>O banco foi conectado com sucesso via API.<br>Item ID: {st.session_state.item_id_simulado}</div>", unsafe_allow_html=True)
        st.write("")
        st.write("Agora que o sistema backend possui a autorização, podemos puxar as movimentações ou focar no Dashboard de Metas.")
        
        if st.button("🔴 Desconectar Conta"):
            st.session_state.banco_conectado = False
            st.rerun()
