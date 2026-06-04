import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import uuid
import time
import os
from supabase import create_client, Client

# ========================================================
# 1. CREDENCIAIS DO BANCO DE DADOS (SUPABASE)
# ========================================================
SUPABASE_URL = "https://tlrrauzylknuatajzniu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRscnJhdXp5bGtudWF0YWp6bml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1MDE5ODMsImV4cCI6MjA5NjA3Nzk4M30.WiTNExA0hJY0AmDY794F7O0ft2SngctNoWQ_LBwyGDk"

# Inicializa a conexão com a nuvem
@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# ========================================================
# 2. CONFIGURAÇÃO VISUAL E CSS PREMIUM
# ========================================================
st.set_page_config(page_title="Fluxo Financeiro PRO", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            font-family: 'Plus Jakarta Sans', sans-serif !important; background-color: #F8FAFC !important; color: #0F172A !important;
        }
        h1, h2, h3 { font-weight: 800 !important; letter-spacing: -1px !important; color: #0F172A !important; }
        .title-gradient {
            background: linear-gradient(90deg, #0284C7 0%, #4F46E5 50%, #7C3AED 100%);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding-bottom: 10px;
        }
        div[data-baseweb="input"], .stSelectbox div { border-radius: 10px !important; }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #0284C7 0%, #4F46E5 100%) !important; border: none !important; color: white !important; font-weight: bold; border-radius: 10px;
        }
        .executive-box { background-color: #FFFFFF; border: 1px solid rgba(15,23,42,0.06); border-radius: 16px; padding: 26px; box-shadow: 0 10px 30px rgba(15,23,42,0.04); }
        .auth-box { background-color: #FFFFFF; padding: 40px; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.05); max-width: 450px; margin: 0 auto; border: 1px solid rgba(79, 70, 229, 0.1); }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. SISTEMA DE AUTENTICAÇÃO (TELA DE LOGIN)
# ========================================================
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if not st.session_state.user_email:
    st.markdown("<h1 class='title-gradient' style='text-align: center; margin-top: 50px;'>Fluxo Financeiro PRO</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Usando o container nativo do Streamlit (sem bugs do quadro branco)
        with st.container(border=True):
            aba_login, aba_registro = st.tabs(["🔒 Entrar", "✨ Criar Conta"])
            
            with aba_login:
                email_login = st.text_input("E-mail corporativo ou pessoal", key="log_email")
                senha_login = st.text_input("Senha de acesso", type="password", key="log_senha")
                if st.button("Acessar Painel", type="primary", use_container_width=True):
                    try:
                        res = supabase.auth.sign_in_with_password({"email": email_login, "password": senha_login})
                        st.session_state.user_email = res.user.email
                        st.rerun()
                    except Exception as e:
                        st.error("E-mail ou senha incorretos. Tente novamente.")
                        
         # --- CÓDIGO DA ABA DE REGISTRO (LOGIN DIRETO) ---
            with aba_registro:
                email_reg = st.text_input("Melhor E-mail", key="reg_email")
                senha_reg = st.text_input("Crie uma Senha Forte", type="password", key="reg_senha")
                
                if st.button("Garantir Meu Acesso", type="primary", use_container_width=True):
                    try:
                        # Regista o utilizador no Supabase
                        res = supabase.auth.sign_up({"email": email_reg, "password": senha_reg})
                        
                        # Mensagem de sucesso sem pedir confirmação de e-mail
                        st.success("✅ Conta criada com sucesso! Pode clicar na aba '🔒 Entrar' ao lado e fazer o seu login agora mesmo.")
                    except Exception as e:
                        st.error("Erro ao criar conta. Verifique os dados inseridos.")
    
    st.stop() # Bloqueia o resto do código até o usuário logar!

# ========================================================
# 4. FUNÇÕES DE BANCO DE DADOS (MULTI-TENANT)
# ========================================================
def carregar_dados():
    try:
        response = supabase.table("lancamentos").select("*").eq("user_email", st.session_state.user_email).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Renomeia para o padrão antigo do visual
            df = df.rename(columns={
                "data_compra": "Data", "competencia": "Competencia", "tipo": "Tipo", "categoria": "Categoria",
                "subcategoria": "Subcategoria", "conta_cartao": "Conta_Cartao", "valor": "Valor",
                "descricao": "Descricao", "parcela": "Parcela", "responsavel": "Responsavel", "status": "Status"
            })
            df["Valor"] = pd.to_numeric(df["Valor"]).fillna(0.0)
            return df
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
    
    return pd.DataFrame(columns=["ID", "Data", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status"])

df = carregar_dados()

def obter_opcoes(coluna, lista_base):
    if not df.empty and coluna in df.columns:
        existentes = df[coluna].dropna().astype(str).unique().tolist()
        return sorted(list(set(lista_base + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])))
    return sorted(lista_base)

# ========================================================
# 5. HEADER DO USUÁRIO LOGADO
# ========================================================
c_head1, c_head2 = st.columns([4, 1])
with c_head1: st.markdown("<h2 class='title-gradient'>Fluxo Financeiro PRO</h2>", unsafe_allow_html=True)
with c_head2:
    st.write(f"👤 {st.session_state.user_email.split('@')[0]}")
    if st.button("Sair (Logout)"):
        st.session_state.user_email = None
        supabase.auth.sign_out()
        st.rerun()

aba_dashboard, aba_lancamentos, aba_openfinance = st.tabs(["📊 Dashboard", "📝 Lançamentos", "🔌 Open Finance"])

# --- DASHBOARD ---
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        col_filtro1, col_filtro2 = st.columns(2)
        with col_filtro1:
            meses_disponiveis = sorted(df["Competencia"].unique(), reverse=True)
            mes_selecionado = st.selectbox("📅 Mês de Cobrança / Fatura", ["Ver Tudo"] + meses_disponiveis)
        
        df_dash = df[df["Competencia"] == mes_selecionado] if mes_selecionado != "Ver Tudo" else df.copy()
        
        t_rec = df_dash[df_dash["Tipo"] == "Receita"]["Valor"].sum()
        t_desp = df_dash[df_dash["Tipo"] == "Despesa"]["Valor"].sum()
        saldo = t_rec - t_desp
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="executive-box" style="border-top: 4px solid #0284C7;"><div class="term-label">Saldo Líquido</div><div class="term-amount" style="color:#0284C7;">R$ {saldo:,.2f}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="executive-box" style="border-top: 4px solid #16A34A;"><div class="term-label">Entradas (+)</div><div class="term-amount" style="color:#16A34A;">R$ {t_rec:,.2f}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="executive-box" style="border-top: 4px solid #DC2626;"><div class="term-label">Saídas (-)</div><div class="term-amount" style="color:#DC2626;">R$ {t_desp:,.2f}</div></div>', unsafe_allow_html=True)
        
        if t_desp > 0:
            st.markdown("<br>", unsafe_allow_html=True)
            fig1 = px.pie(df_dash[df_dash["Tipo"] == "Despesa"], values="Valor", names="Categoria", title="Despesas por Categoria", hole=0.4)
            st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("O Dashboard está aguardando lançamentos.")

# --- LANÇAMENTOS (SALVANDO NA NUVEM) ---
with aba_lancamentos:
    st.subheader("Registrar Movimentação")
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
        data_lancamento = st.date_input("Data da Compra")
        mes_fatura = st.date_input("Mês da Fatura")
        valor_total = st.number_input("Valor Total (R$)", min_value=0.0)
    with col2:
        parcelas = st.number_input("Parcelas", min_value=1, max_value=120, value=1)
        categoria = st.selectbox("Categoria", obter_opcoes("Categoria", ["Alimentação", "Transporte", "Moradia", "Salário"]))
    with col3:
        conta_cartao = st.selectbox("Conta", obter_opcoes("Conta_Cartao", ["Nubank", "Inter", "Pix"]))
        descricao = st.text_input("Descrição")

    if st.button("💾 Lançar no Sistema", type="primary") and valor_total > 0:
        novas_linhas = []
        valor_parc = valor_total / parcelas
        for i in range(parcelas):
            m = mes_fatura.month - 1 + i
            y = mes_fatura.year + (m // 12)
            comp = f"{y}-{(m % 12) + 1:02d}"
            
            # Formato exato do Banco de Dados Supabase (SQL)
            novas_linhas.append({
                "user_email": st.session_state.user_email,
                "data_compra": data_lancamento.strftime("%Y-%m-%d"),
                "competencia": comp,
                "tipo": tipo, "categoria": categoria, "subcategoria": "Geral",
                "conta_cartao": conta_cartao, "valor": float(round(valor_parc, 2)),
                "descricao": descricao, "parcela": f"{i+1}/{parcelas}" if parcelas > 1 else "À vista",
                "responsavel": "Eu", "status": "Pago"
            })
            
        supabase.table("lancamentos").insert(novas_linhas).execute()
        st.success("Lançamento salvo diretamente na Nuvem Supabase!")
        time.sleep(1.5)
        st.rerun()

# --- OPEN FINANCE ---
with aba_openfinance:
    st.subheader("🔌 Hub de Integração Aberta")
    st.info("A infraestrutura do banco de dados na nuvem (Supabase) foi configurada com sucesso. A conexão via Hub Integrador será iniciada na próxima etapa.")
