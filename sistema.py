import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
from supabase import create_client, Client
import google.generativeai as genai
import extra_streamlit_components as stx

# ========================================================
# 1. CREDENCIAIS BASE E DOCUMENTAÇÃO
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

# 🔥 SOLUÇÃO DEFINITIVA DA IA: Seleção Dinâmica de Modelo 🔥
if GEMINI_API_KEY and GEMINI_API_KEY.strip() != "":
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        # Pede à Google a lista de modelos permitidos para esta chave
        modelos_disponiveis = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if modelos_disponiveis:
            # Pega o primeiro modelo compatível da lista real
            modelo_ia = genai.GenerativeModel(modelos_disponiveis[0])
        else:
            # Fallback em caso de lista vazia
            modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        modelo_ia = genai.GenerativeModel('gemini-1.5-flash')
else:
    modelo_ia = None

# ========================================================
# 2. CONFIGURAÇÃO VISUAL E CSS
# ========================================================
st.set_page_config(page_title="Fluxo Financeiro PRO", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { font-family: 'Plus Jakarta Sans', sans-serif !important; background-color: #F3F4F6 !important; color: #0F172A !important; }
        h1, h2, h3, h4 { font-weight: 800 !important; letter-spacing: -0.5px !important; color: #1E293B !important; }
        .title-gradient { background: linear-gradient(90deg, #0284C7 0%, #4F46E5 50%, #7C3AED 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; padding-bottom: 10px; }
        div[data-baseweb="input"], .stSelectbox div { border-radius: 6px !important; }
        div.stButton > button[kind="primary"] { background: linear-gradient(90deg, #0284C7 0%, #4F46E5 100%) !important; border: none !important; color: white !important; font-weight: bold; border-radius: 6px; padding: 10px; }
        
        [data-testid="stMetricValue"] { font-size: 28px !important; font-weight: 800 !important; }
        [data-testid="stMetricLabel"] { font-size: 14px !important; font-weight: 600 !important; color: #64748B !important; }
        div[data-testid="metric-container"] { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
        hr { margin-top: 20px; margin-bottom: 20px; border: 0; border-top: 1px solid #E2E8F0; }
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. AUTENTICAÇÃO E RESOLUÇÃO DE NOME
# ========================================================
def extrair_nome_de_email(email):
    if not email: return "Usuário"
    return email.split("@")[0].split(".")[0].split("_")[0].split("-")[0].capitalize()

if "user_email" not in st.session_state: st.session_state.user_email = None
if "user_nome" not in st.session_state: st.session_state.user_nome = None

cookie_manager = stx.CookieManager(key="auth_cookies_v9")
cookies = cookie_manager.get_all()

if st.session_state.user_email is None and cookies and "u_mail" in cookies and cookies["u_mail"]:
    st.session_state.user_email = cookies["u_mail"]

if st.session_state.user_email and (not st.session_state.user_nome or st.session_state.user_nome == "Usuário"):
    nome_cookie = cookies.get("u_name") if cookies else None
    if nome_cookie and nome_cookie != "Usuário": st.session_state.user_nome = nome_cookie
    else: st.session_state.user_nome = extrair_nome_de_email(st.session_state.user_email)

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
                        nome_metadado = res.user.user_metadata.get("primeiro_nome") if res.user and res.user.user_metadata else None
                        nome_final = nome_metadado if nome_metadado else extrair_nome_de_email(res.user.email)
                        st.session_state.user_nome = nome_final
                        cookie_manager.set("u_mail", res.user.email, max_age=30*24*60*60, key="login_mail")
                        cookie_manager.set("u_name", nome_final, max_age=30*24*60*60, key="login_name")
                        time.sleep(0.5)
                        st.rerun()
                    except Exception as e: st.error(f"Erro no login: {e}")
            with aba_registro:
                nome_reg = st.text_input("Seu primeiro nome:", key="reg_nome")
                email_reg = st.text_input("Seu e-mail:", key="reg_email")
                senha_reg = st.text_input("Crie uma Senha Forte:", type="password", key="reg_senha")
                if st.button("Garantir Acesso", type="primary", use_container_width=True):
                    if nome_reg.strip() and email_reg.strip():
                        try:
                            supabase.auth.sign_up({"email": email_reg, "password": senha_reg, "options": {"data": {"primeiro_nome": nome_reg.strip()}}})
                            st.success(f"Conta de {nome_reg} criada! Faça login.")
                        except Exception as e: st.error(f"Erro: {e}")
    st.stop()

# ========================================================
# 4. GESTÃO DE MASTER DATA E LISTAS BASE
# ========================================================
LISTA_RESP_BASE = [st.session_state.user_nome if st.session_state.user_nome else "Gabriel", "Roberson", "Família", "Empresa"]
LISTA_BANC_BASE = ["Banco do Brasil", "Inter", "Nubank", "Itaú", "Bradesco", "PicPay", "Mercado Pago"]
LISTA_CAT_DESP = ["Alimentação", "Transporte", "Moradia", "Salário", "Assinaturas", "Saúde", "Impostos", "Vestuário", "Outros"]
LISTA_CAT_REC = ["Salário / Pró-Labore", "Reembolsos / Estornos", "Rendimentos (Dividendos / JCP)", "Vendas", "Outros"]
LISTA_CAT_INV = ["Ações (B3)", "Fundos Imobiliários (FIIs)", "Renda Fixa", "Criptomoedas", "Ações (EUA)"]
LISTA_ORIG_BASE = ["Supermercado", "Pix", "Empresa", "Cliente", "Shein", "Roberson"]
SUBCATS_BASE = ["Aluguel", "Energia", "Internet", "Água", "Condomínio", "Alimentação", "Software", "Reembolso de Terceiros", "Estorno de Compra", "Geral"]

@st.cache_data(ttl=5)
def carregar_dados_completos(email):
    try:
        res = supabase.table("lancamentos").select("*").eq("user_email", email).execute()
        if res.data:
            df_t = pd.DataFrame(res.data)
            if "mes_pagamento" not in df_t.columns: df_t["mes_pagamento"] = df_t["competencia"]
            df_t["mes_pagamento"] = df_t["mes_pagamento"].fillna(df_t["competencia"])
            df_t = df_t.rename(columns={"id": "ID", "data_compra": "Data", "competencia": "Competencia", "mes_pagamento": "Mes_Pagamento", "tipo": "Tipo", "categoria": "Categoria", "subcategoria": "Subcategoria", "conta_cartao": "Conta_Cartao", "valor": "Valor", "descricao": "Descricao", "parcela": "Parcela", "responsavel": "Responsavel", "status": "Status", "origem_destino": "Origem_Destino"})
            df_t["Valor"] = pd.to_numeric(df_t["Valor"]).fillna(0.0)
            return df_t
    except: pass
    return pd.DataFrame(columns=["ID", "Data", "Mes_Pagamento", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status", "Origem_Destino"])

df_tudo = carregar_dados_completos(st.session_state.user_email)
df_configs = df_tudo[df_tudo["Tipo"].str.startswith("Config_")].copy() if not df_tudo.empty else pd.DataFrame(columns=df_tudo.columns)
df = df_tudo[~df_tudo["Tipo"].str.startswith("Config_")].copy() if not df_tudo.empty else pd.DataFrame(columns=df_tudo.columns)
df_cartoes = df_configs[df_configs["Tipo"] == "Config_Cartao"]

def obter_opcoes(coluna, lista_base):
    configs = df_configs[df_configs["Tipo"] == f"Config_{coluna}"][coluna].dropna().astype(str).unique().tolist() if not df_configs.empty and coluna in df_configs.columns else []
    existentes = df[coluna].dropna().astype(str).unique().tolist() if not df.empty and coluna in df.columns else []
    ocultos = df_configs[(df_configs["Tipo"] == "Config_Excluida") & (df_configs["Categoria"] == coluna)]["Subcategoria"].dropna().astype(str).unique().tolist() if not df_configs.empty else []
    todos = set(lista_base + configs + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])
    for item in ocultos:
        if item in todos: todos.remove(item)
    return sorted(list(todos))

def obter_subcategorias_dinamicas(categoria_alvo):
    configs = df_configs[(df_configs["Tipo"] == "Config_Subcategoria") & (df_configs["Categoria"] == categoria_alvo)]["Subcategoria"].dropna().astype(str).unique().tolist() if not df_configs.empty else []
    existentes = df[df["Categoria"] == categoria_alvo]["Subcategoria"].dropna().astype(str).unique().tolist() if not df.empty and "Subcategoria" in df.columns else []
    ocultos = df_configs[(df_configs["Tipo"] == "Config_Excluida") & (df_configs["Categoria"] == "Subcategoria")]["Subcategoria"].dropna().astype(str).unique().tolist() if not df_configs.empty else []
    todos = set(SUBCATS_BASE + configs + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])
    for item in ocultos:
        if item in todos: todos.remove(item)
    return sorted(list(todos))

# ========================================================
# 5. HEADER
# ========================================================
c_head1, c_head2 = st.columns([4, 1])
with c_head1: st.markdown("<h2 class='title-gradient'>Fluxo Financeiro PRO</h2>", unsafe_allow_html=True)
with c_head2:
    st.markdown(f"<div style='text-align: right; padding-top: 15px;'><span style='font-size:18px;'>👤 Olá, <b>{st.session_state.user_nome}</b></span></div>", unsafe_allow_html=True)
    if st.button("Sair (Logout)", use_container_width=True):
        cookie_manager.delete("u_mail", key="logout_del_mail")
        cookie_manager.delete("u_name", key="logout_del_name")
        st.session_state.clear()
        time.sleep(0.5) 
        st.rerun()

aba_dashboard, aba_lancamentos, aba_cadastros, aba_assistente = st.tabs(["📊 Inteligência Financeira", "📝 Lançamentos", "⚙️ Central de Cadastros", "🤖 Assistente IA"])

# ========================================================
# 6. SUPER DASHBOARD UNIFICADO (BI + VHSYS STYLE)
# ========================================================
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        dash_geral, dash_investimentos = st.tabs(["📊 Visão Global & Faturas", "📈 Carteira de Investimentos"])
        
        with dash_geral:
            st.markdown("#### 🎯 Como você deseja analisar seus dados hoje?")
            c_mode, c_mes = st.columns([2, 1])
            with c_mode:
                modo_visao = st.radio("Modo de Análise Mestre:", 
                                      ["💳 Fatura / Contas a Pagar (Quando o dinheiro sai/entra)", 
                                       "🛒 Regime de Caixa (Quando a compra realmente aconteceu)"], 
                                      horizontal=True)
                col_filtro = "Mes_Pagamento" if "Fatura" in modo_visao else "Competencia"
            with c_mes:
                meses_disp = ["Todos os Meses"] + sorted(df[col_filtro].dropna().unique(), reverse=True)
                mes_sel = st.selectbox(f"Selecione o Mês ({'Fatura' if 'Fatura' in modo_visao else 'Compra'}):", meses_disp)

            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1:
                lista_contas = ["Todas as Contas / Cartões"] + sorted(df["Conta_Cartao"].dropna().unique())
                conta_sel = st.selectbox("Conta ou Cartão:", lista_contas)
            with c_f2:
                todos_responsaveis = obter_opcoes("Responsavel", LISTA_RESP_BASE)
                resp_sel = st.multiselect("Responsável:", todos_responsaveis, default=todos_responsaveis)
            with c_f3:
                status_sel = st.selectbox("Status Geral:", ["Todos", "Pago", "Pendente"])
            
            df_dash = df.copy()
            if mes_sel != "Todos os Meses": df_dash = df_dash[df_dash[col_filtro] == mes_sel]
            if conta_sel != "Todas as Contas / Cartões": df_dash = df_dash[df_dash["Conta_Cartao"] == conta_sel]
            
            if resp_sel:
                df_dash = df_dash[df_dash["Responsavel"].apply(lambda x: any(r in str(x) for r in resp_sel))]
            else: 
                df_dash = df_dash.iloc[0:0]
                
            if status_sel != "Todos": df_dash = df_dash[df_dash["Status"] == status_sel]
            
            t_rec_pago = df_dash[(df_dash["Tipo"] == "Receita") & (df_dash["Status"] == "Pago")]["Valor"].sum()
            t_rec_pend = df_dash[(df_dash["Tipo"] == "Receita") & (df_dash["Status"] == "Pendente")]["Valor"].sum()
            t_desp_pago = df_dash[(df_dash["Tipo"] == "Despesa") & (df_dash["Status"] == "Pago")]["Valor"].sum()
            t_desp_pend = df_dash[(df_dash["Tipo"] == "Despesa") & (df_dash["Status"] == "Pendente")]["Valor"].sum()
            t_inv = df_dash[df_dash["Tipo"] == "Investimento"]["Valor"].sum()
            saldo_real = t_rec_pago - t_desp_pago
            
            df_receitas = df_dash[df_dash["Tipo"] == "Receita"]
            conta_top = df_receitas.groupby("Conta_Cartao")["Valor"].sum().idxmax() if not df_receitas.empty else "Nenhuma"
            
            df_despesas = df_dash[df_dash["Tipo"] == "Despesa"]
            cat_gasto_top = df_despesas.groupby("Categoria")["Valor"].sum().idxmax() if not df_despesas.empty else "Nenhuma"
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("##### 💰 Visão de Caixa Real (Apenas o que já foi Pago/Recebido)")
            cm1, cm2, cm3, cm4 = st.columns(4)
            cm1.metric(label="Saldo Real na Conta", value=f"R$ {saldo_real:,.2f}", delta="Positivo" if saldo_real >= 0 else "Negativo", delta_color="normal")
            cm2.metric(label="Total Recebido (Entrou)", value=f"R$ {t_rec_pago:,.2f}")
            cm3.metric(label="Total Pago (Saiu)", value=f"R$ {t_desp_pago:,.2f}", delta_color="inverse")
            cm4.metric(label="Total Investido", value=f"R$ {t_inv:,.2f}", delta_color="off")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("##### ⏳ Controle de Contas a Pagar e Receber (Pendentes)")
            cp1, cp2, cp3, cp4 = st.columns(4)
            cp1.metric(label="A Receber (Esperado)", value=f"R$ {t_rec_pend:,.2f}", delta="Dinheiro a entrar")
            cp2.metric(label="A Pagar (Dívidas/Fatura)", value=f"R$ {t_desp_pend:,.2f}", delta="Dinheiro a sair", delta_color="inverse")
            cp3.metric(label="🏆 Conta c/ Mais Entradas", value=str(conta_top))
            cp4.metric(label="🚨 Categoria c/ Mais Gastos", value=str(cat_gasto_top))
            
            st.markdown("---")
            if not df_dash.empty:
                st.markdown("##### 📅 Linha do Tempo: Frequência de Compras e Entradas")
                df_timeline = df_dash.groupby(["Data", "Tipo"])["Valor"].sum().reset_index().sort_values(by="Data")
                
                fig_time = px.bar(df_timeline, x="Data", y="Valor", color="Tipo", 
                                  color_discrete_map={"Despesa": "#EF4444", "Receita": "#10B981", "Investimento": "#6366F1"}, 
                                  barmode="group", text_auto='.2s')
                fig_time.update_layout(margin=dict(t=10, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend_title_text='')
                fig_time.update_xaxes(type='category', title="", showgrid=False)
                fig_time.update_yaxes(title="", showgrid=True, gridcolor='#E2E8F0')
                st.plotly_chart(fig_time, use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                
                cg1, cg2 = st.columns(2)
                with cg1: 
                    with st.container(border=True):
                        st.markdown("##### 🍕 Para onde o dinheiro está indo?")
                        if not df_despesas.empty: 
                            fig_pie = px.pie(df_despesas, values="Valor", names="Categoria", hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
                            fig_pie.update_layout(margin=dict(t=10, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_pie, use_container_width=True)
                        else: st.info("Sem despesas neste filtro para exibir o gráfico.")
                with cg2:
                    with st.container(border=True):
                        st.markdown("##### 🏆 Top 5 Maiores Gastos Gerais")
                        if not df_despesas.empty: 
                            df_top_despesas = df_despesas.groupby("Descricao")["Valor"].sum().reset_index().sort_values("Valor").tail(5)
                            fig_bar = px.bar(df_top_despesas, x="Valor", y="Descricao", orientation='h', color_discrete_sequence=['#EF4444'])
                            fig_bar.update_layout(margin=dict(t=10, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            fig_bar.update_xaxes(title="", showgrid=True, gridcolor='#E2E8F0')
                            fig_bar.update_yaxes(title="")
                            st.plotly_chart(fig_bar, use_container_width=True)
                        else: st.info("Sem despesas neste filtro para exibir o gráfico.")

                if not df_despesas.empty:
                    st.markdown("---")
                    st.markdown("### 🔎 Análise Profunda por Categoria (Drill-down)")
                    st.write("Selecione uma Categoria específica do gráfico de pizza para descobrir exatamente o que gerou esses custos.")
                    
                    cat_pior = df_despesas.groupby("Categoria")["Valor"].sum().idxmax()
                    lista_cat_disponiveis = sorted(df_despesas["Categoria"].unique().tolist())
                    
                    c_drill, _ = st.columns([1, 2])
                    with c_drill:
                        cat_investigar = st.selectbox("Selecione a Categoria para investigar:", lista_cat_disponiveis, index=lista_cat_disponiveis.index(cat_pior))
                    
                    df_investigacao = df_despesas[df_despesas["Categoria"] == cat_investigar]
                    
                    cd1, cd2 = st.columns(2)
                    with cd1:
                        with st.container(border=True):
                            st.markdown(f"##### Divisão de **{cat_investigar}** por Subcategoria")
                            fig_sub = px.pie(df_investigacao, values="Valor", names="Subcategoria", hole=0.5, color_discrete_sequence=px.colors.sequential.Teal)
                            fig_sub.update_layout(margin=dict(t=10, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(fig_sub, use_container_width=True)
                            
                    with cd2:
                        with st.container(border=True):
                            st.markdown(f"##### Exatamente onde gastou em **{cat_investigar}**?")
                            df_top_sub = df_investigacao.groupby("Descricao")["Valor"].sum().reset_index().sort_values("Valor")
                            fig_bar_sub = px.bar(df_top_sub, x="Valor", y="Descricao", orientation='h', color_discrete_sequence=['#F59E0B'])
                            fig_bar_sub.update_layout(margin=dict(t=10, b=0, l=0, r=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                            fig_bar_sub.update_xaxes(title="", showgrid=True, gridcolor='#E2E8F0')
                            fig_bar_sub.update_yaxes(title="")
                            st.plotly_chart(fig_bar_sub, use_container_width=True)

            st.markdown("---")
            st.markdown("##### 💳 Detalhamento das Movimentações (Extrato)")
            if not df_dash.empty:
                df_extrato = df_dash[["Data", "Competencia", "Mes_Pagamento", "Conta_Cartao", "Descricao", "Categoria", "Valor", "Status"]].sort_values(by="Data", ascending=False)
                st.dataframe(df_extrato, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhuma transação encontrada com os filtros selecionados.")

        with dash_investimentos:
            st.markdown("### 📈 Sua Carteira de Ativos")
            df_invest = df[df["Tipo"] == "Investimento"].copy()
            df_prov = df[(df["Tipo"] == "Receita") & (df["Categoria"].str.contains("Dividendos|JCP|Rendimentos", case=False, na=False))].copy()
            
            if not df_invest.empty:
                t_aportado = df_invest["Valor"].sum()
                t_proventos = df_prov["Valor"].sum() if not df_prov.empty else 0.0
                
                cp1, cp2, cp3 = st.columns(3)
                cp1.metric(label="Total Aportado Histórico", value=f"R$ {t_aportado:,.2f}")
                cp2.metric(label="Proventos Recebidos (JCP/Div)", value=f"R$ {t_proventos:,.2f}", delta="Cashback na Conta")
                cp3.metric(label="Ativos na Carteira", value=f"{df_invest['Subcategoria'].nunique()} tickers")
                
                st.markdown("<br>", unsafe_allow_html=True)
                ca1, ca2 = st.columns(2)
                with ca1:
                    df_grupo_ativos = df_invest.groupby("Subcategoria")["Valor"].sum().reset_index()
                    st.plotly_chart(px.pie(df_grupo_ativos, values="Valor", names="Subcategoria", title="Alocação por Ativo", hole=0.4), use_container_width=True)
                with ca2:
                    df_grupo_classe = df_invest.groupby("Categoria")["Valor"].sum().reset_index()
                    st.plotly_chart(px.bar(df_grupo_classe, x="Categoria", y="Valor", title="Alocação por Classe de Investimento", color="Categoria"), use_container_width=True)
                
                st.markdown("#### Extrato de Aportes")
                st.dataframe(df_invest[["Data", "Categoria", "Subcategoria", "Origem_Destino", "Valor"]].rename(columns={"Subcategoria": "Ticker", "Origem_Destino": "Corretora"}), use_container_width=True, hide_index=True)
            else:
                st.info("Você ainda não registrou nenhum Investimento. Use a aba de Lançamentos para criar seu portfólio.")

# ========================================================
# 7. LANÇAMENTOS INTELIGENTES E MESA DE OPERAÇÕES
# ========================================================
def auto_salvar_cadastro(tipo_cad, valor, vinculada=""):
    try: 
        cat_val = valor if tipo_cad == "Categoria" else (vinculada if tipo_cad == "Subcategoria" else "")
        sub_val = valor if tipo_cad == "Subcategoria" else ""
        supabase.table("lancamentos").insert({"user_email": st.session_state.user_email, "data_compra": datetime.now().strftime("%Y-%m-%d"), "competencia": datetime.now().strftime("%Y-%m"), "mes_pagamento": datetime.now().strftime("%Y-%m"), "tipo": f"Config_{tipo_cad}", "categoria": cat_val, "subcategoria": sub_val, "responsavel": valor if tipo_cad == "Responsavel" else "", "origem_destino": valor if tipo_cad == "Origem_Destino" else "", "conta_cartao": "", "valor": 0.0, "descricao": "Configuração Automática", "parcela": "-", "status": "Config"}).execute()
    except: pass

with aba_lancamentos:
    aba_manual, aba_gerenciar = st.tabs(["✍️ Painel de Lançamento", "✏️ Editar Histórico"])
    
    with aba_manual:
        with st.container(border=True):
            c_tipo, c_val, c_data = st.columns(3)
            with c_tipo: tipo_mov = st.selectbox("O que vamos lançar hoje?", ["Despesa", "Receita", "Investimento"])
            with c_val: valor_total = st.number_input("Qual o Valor (R$)?", min_value=0.0, format="%.2f")
            with c_data: data_ocorreu = st.date_input("Qual a Data?")

        with st.container(border=True):
            st.markdown(f"#### Detalhes: {tipo_mov}")
            
            if tipo_mov == "Despesa":
                c4, c_sub, c5, c6 = st.columns(4)
                with c4: 
                    cat_sel = st.selectbox("Categoria do Gasto", obter_opcoes("Categoria", LISTA_CAT_DESP) + ["➕ Nova..."])
                    categoria = st.text_input("Nova Categoria:") if cat_sel == "➕ Nova..." else cat_sel
                with c_sub:
                    opcoes_subcat = obter_subcategorias_dinamicas(categoria) + ["➕ Nova Subcategoria..."]
                    subcat_sel = st.selectbox("Subcategoria", opcoes_subcat)
                    subcategoria = st.text_input("Nova Subcategoria:") if subcat_sel == "➕ Nova Subcategoria..." else subcat_sel
                with c5:
                    conta_sel = st.selectbox("Cartão ou Conta Usada", ["Conta Corrente", "Pix", "Dinheiro Físico"] + (df_cartoes["Conta_Cartao"].unique().tolist() if not df_cartoes.empty else []) + ["➕ Novo Cartão/Conta..."])
                    conta_cartao = st.text_input("Nova Conta:") if conta_sel == "➕ Novo Cartão/Conta..." else conta_sel
                with c6:
                    orig_sel = st.selectbox("Fornecedor / Loja", obter_opcoes("Origem_Destino", LISTA_ORIG_BASE) + ["➕ Novo Fornecedor..."])
                    origem_destino = st.text_input("Nome do Fornecedor:") if orig_sel == "➕ Novo Fornecedor..." else orig_sel
                
                c7, c8 = st.columns(2)
                with c7: desc_resumo = st.text_input("Descrição Resumida (Ex: Uber, Aluguel)")
                with c8: 
                    opcoes_resp = obter_opcoes("Responsavel", LISTA_RESP_BASE)
                    resp_lista = st.multiselect("Responsáveis (Quem vai dividir?)", opcoes_resp, default=[st.session_state.user_nome if st.session_state.user_nome else "Gabriel"])
                
                st.markdown("##### 📅 Datas Fiscais (Mês da Compra vs Pagamento da Fatura)")
                md1, md2, md3, md4 = st.columns(4)
                meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
                with md1: ano_comp = st.selectbox("Ano da Compra", [2024, 2025, 2026, 2027], index=2)
                with md2: mes_comp = st.selectbox("Mês da Compra", meses_nomes, index=datetime.now().month - 1)
                with md3: ano_pag = st.selectbox("Ano de Pagamento (Fatura)", [2024, 2025, 2026, 2027], index=2)
                with md4: mes_pag = st.selectbox("Mês de Pagamento (Fatura)", meses_nomes, index=datetime.now().month - 1)
                
                st.markdown("---")
                cf1, cf2 = st.columns(2)
                with cf1: 
                    tipo_frequencia = st.radio("Como foi o pagamento?", ["À vista (Único)", "Parcelado"], horizontal=True)
                    parcelas = st.number_input("Quantidade de Parcelas", 2, 120, 2) if tipo_frequencia == "Parcelado" else 1
                with cf2: status_final = st.selectbox("A fatura/conta já foi paga?", ["Pendente", "Pago"])
                
                ativo_ticker = ""

            elif tipo_mov == "Receita":
                c4, c_sub_rec, c5 = st.columns(3)
                with c4: 
                    cat_sel = st.selectbox("Tipo de Receita", obter_opcoes("Categoria", LISTA_CAT_REC) + ["➕ Nova..."])
                    categoria = st.text_input("Nova Receita:") if cat_sel == "➕ Nova..." else cat_sel
                with c_sub_rec:
                    opcoes_subcat_rec = obter_subcategorias_dinamicas(categoria) + ["➕ Nova Subcategoria..."]
                    subcat_sel = st.selectbox("Subcategoria", opcoes_subcat_rec)
                    subcategoria = st.text_input("Nova Subcategoria:") if subcat_sel == "➕ Nova Subcategoria..." else subcat_sel
                with c5:
                    if "Dividendos" in categoria or "JCP" in categoria or "Rendimentos" in categoria:
                        ativo_ticker = st.text_input("Ticker que pagou (Ex: MXRF11)").upper()
                        orig_sel = "Bolsa / B3"
                        origem_destino = orig_sel
                    else:
                        ativo_ticker = ""
                        orig_sel = st.selectbox("Quem pagou? (Origem)", obter_opcoes("Origem_Destino", LISTA_ORIG_BASE) + ["➕ Novo Pagador..."])
                        origem_destino = st.text_input("Novo Pagador:") if orig_sel == "➕ Novo Pagador..." else orig_sel
                        
                c6, c7, c8 = st.columns(3)
                with c6:
                    lista_contas_receita = ["Conta Corrente", "Pix", "Corretora", "Dinheiro Físico"] + (df_cartoes["Conta_Cartao"].unique().tolist() if not df_cartoes.empty else []) + ["➕ Novo Cartão/Conta..."]
                    conta_sel = st.selectbox("Onde o dinheiro entrou?", lista_contas_receita)
                    conta_cartao = st.text_input("Novo Cartão/Conta:") if conta_sel == "➕ Novo Cartão/Conta..." else conta_sel
                with c7: desc_resumo = st.text_input("Descrição (Ex: Salário, Reembolso Shein)")
                with c8: 
                    resp_principal = st.selectbox("Titular / Beneficiário", obter_opcoes("Responsavel", LISTA_RESP_BASE))
                    resp_lista = [resp_principal]
                
                st.markdown("##### 📅 Status da Entrada")
                cr1, cr2 = st.columns(2)
                with cr1:
                    status_vis = st.radio("O dinheiro já está na conta / cartão?", ["Sim (Recebido/Pago)", "Ainda não (A Receber)"], horizontal=True)
                    status_final = "Pago" if "Sim" in status_vis else "Pendente"
                with cr2:
                    tipo_frequencia = "Único"
                    parcelas = 1
                
                meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
                ano_comp = ano_pag = data_ocorreu.year 
                mes_comp = mes_pag = meses_nomes[data_ocorreu.month - 1]

            else: 
                st.info("💡 Investimento é construção de patrimônio. A ordem é executada e o dinheiro transferido.")
                c4, c5, c6 = st.columns(3)
                with c4: 
                    cat_sel = st.selectbox("Classe de Ativo", obter_opcoes("Categoria", LISTA_CAT_INV) + ["➕ Nova..."])
                    categoria = st.text_input("Nova Classe:") if cat_sel == "➕ Nova..." else cat_sel
                with c5:
                    ativo_ticker = st.text_input("Qual o Ticker/Ativo? (Ex: ITUB4, Tesouro Selic)").upper()
                    subcategoria = ativo_ticker
                with c6:
                    conta_cartao = st.selectbox("Dinheiro saiu de qual conta?", ["Conta Corrente", "Pix", "Poupança"])
                    
                c7, c8 = st.columns(2)
                with c7: 
                    orig_sel = st.selectbox("Para qual Corretora foi?", obter_opcoes("Origem_Destino", ["XP", "BTG", "NuInvest", "Rico", "Binance"]) + ["➕ Nova..."])
                    origem_destino = st.text_input("Nova Corretora:") if orig_sel == "➕ Nova..." else orig_sel
                with c8: 
                    desc_resumo = f"Aporte em {ativo_ticker}" if ativo_ticker else "Aporte de Investimento"
                    resp_principal = st.selectbox("Titular da Conta", obter_opcoes("Responsavel", LISTA_RESP_BASE))
                    resp_lista = [resp_principal]
                    
                tipo_frequencia = "Único"
                parcelas = 1
                status_final = "Pago" 
                
                meses_nomes = ["01 - Janeiro", "02 - Fevereiro", "03 - Março", "04 - Abril", "05 - Maio", "06 - Junho", "07 - Julho", "08 - Agosto", "09 - Setembro", "10 - Outubro", "11 - Novembro", "12 - Dezembro"]
                ano_comp = ano_pag = data_ocorreu.year
                mes_comp = mes_pag = meses_nomes[data_ocorreu.month - 1]

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Concluir Lançamento", type="primary", use_container_width=True):
            if valor_total > 0 and categoria and resp_lista:
                if cat_sel == "➕ Nova..." and categoria: auto_salvar_cadastro("Categoria", categoria)
                if tipo_mov == "Despesa" and subcat_sel == "➕ Nova Subcategoria..." and subcategoria: auto_salvar_cadastro("Subcategoria", subcategoria, categoria)
                if conta_sel == "➕ Novo Cartão/Conta..." and conta_cartao: auto_salvar_cadastro("Cartao", conta_cartao)
                
                if orig_sel == "➕ Novo Fornecedor..." and origem_destino: auto_salvar_cadastro("Origem_Destino", origem_destino)
                if orig_sel == "➕ Novo Pagador..." and origem_destino: auto_salvar_cadastro("Origem_Destino", origem_destino)
                if orig_sel == "➕ Nova..." and origem_destino: auto_salvar_cadastro("Origem_Destino", origem_destino)
                
                if ativo_ticker and tipo_mov == "Receita": desc_resumo = f"[{ativo_ticker}] {desc_resumo}"

                novas_linhas = []
                start_m_comp = int(mes_comp.split(" - ")[0])
                start_m_pag = int(mes_pag.split(" - ")[0])
                num_pessoas = len(resp_lista)
                
                for i in range(parcelas):
                    comp_str = f"{int(ano_comp) + ((start_m_comp - 1 + i) // 12)}-{((start_m_comp - 1 + i) % 12) + 1:02d}"
                    pag_str = f"{int(ano_pag) + ((start_m_pag - 1 + i) // 12)}-{((start_m_pag - 1 + i) % 12) + 1:02d}"
                    val_parcela = valor_total / parcelas if tipo_frequencia == "Parcelado" else valor_total
                    val_por_pessoa = val_parcela / num_pessoas
                    
                    for pessoa in resp_lista:
                        desc_final = f"{desc_resumo} ({i+1}/{parcelas})" if tipo_frequencia == "Parcelado" else desc_resumo
                        if num_pessoas > 1: desc_final += " (Rateio)"
                        
                        status_laco = status_final if i == 0 or status_final != "Pago" else "Pendente"
                        if tipo_mov in ["Investimento", "Receita"] and status_final == "Pago": status_laco = "Pago"
                        
                        novas_linhas.append({
                            "user_email": st.session_state.user_email, 
                            "data_compra": str(data_ocorreu), 
                            "competencia": comp_str, 
                            "mes_pagamento": pag_str, 
                            "tipo": tipo_mov, 
                            "categoria": categoria, 
                            "subcategoria": subcategoria, 
                            "conta_cartao": conta_cartao, 
                            "valor": float(round(val_por_pessoa, 2)), 
                            "descricao": desc_final, 
                            "parcela": f"{i+1}/{parcelas}" if tipo_frequencia == "Parcelado" else "Único", 
                            "responsavel": pessoa, 
                            "origem_destino": origem_destino, 
                            "status": status_laco
                        })

                try:
                    supabase.table("lancamentos").insert(novas_linhas).execute()
                    st.success("Operação Registrada e Dividida com Sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Erro no banco de dados: {e}")
            else: st.warning("Preencha o Valor e a Categoria obrigatórios!")

    with aba_gerenciar:
        st.markdown("### ✏️ Edição de Histórico")
        if not df.empty:
            df_view = df[["ID", "Data", "Mes_Pagamento", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Descricao", "Valor", "Status"]].copy()
            
            c_f1, c_f2, c_f3 = st.columns(3)
            with c_f1: filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "Despesa", "Receita", "Investimento"])
            with c_f2: filtro_mes = st.selectbox("Filtrar por Mês de Pagamento", ["Todos"] + sorted(df_view["Mes_Pagamento"].unique(), reverse=True))
            with c_f3: filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Pago", "Pendente"])
            
            if filtro_tipo != "Todos": df_view = df_view[df_view["Tipo"] == filtro_tipo]
            if filtro_mes != "Todos": df_view = df_view[df_view["Mes_Pagamento"] == filtro_mes]
            if filtro_status != "Todos": df_view = df_view[df_view["Status"] == filtro_status]
            
            st.markdown("---")
            selecionar_tudo = st.checkbox("☑️ Selecionar todos os lançamentos visíveis abaixo", value=False)
            df_view.insert(0, "Selecionar", selecionar_tudo)
            
            df_resultado = st.data_editor(df_view, hide_index=True, use_container_width=True, disabled=["ID"])
            ids_selecionados = df_resultado[df_resultado["Selecionar"] == True]["ID"].tolist()
            
            if "confirmar_delecao" in st.session_state and st.session_state.confirmar_delecao:
                st.error(f"⚠️ **Confirmação:** Apagar {len(st.session_state.confirmar_delecao)} lançamentos permanentemente?")
                col_sim, col_nao = st.columns(2)
                with col_sim:
                    if st.button("🚨 SIM, APAGAR DEFINITIVAMENTE", use_container_width=True):
                        try:
                            supabase.table("lancamentos").delete().in_("id", st.session_state.confirmar_delecao).execute()
                            st.session_state.confirmar_delecao = False
                            st.success("Removidos com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e: st.error(f"Erro: {e}")
                with col_nao:
                    if st.button("✅ CANCELAR", type="primary", use_container_width=True):
                        st.session_state.confirmar_delecao = False
                        st.rerun()
            else:
                c_op1, c_op2, c_op3, c_op4 = st.columns(4)
                with c_op1:
                    if st.button("💾 Salvar Edições Manuais", type="primary", use_container_width=True):
                        try:
                            mudancas = 0
                            for idx in range(len(df_resultado)):
                                row_ed = df_resultado.iloc[idx]
                                if not row_ed["Selecionar"]:
                                    supabase.table("lancamentos").update({
                                        "data_compra": str(row_ed["Data"]),
                                        "mes_pagamento": str(row_ed["Mes_Pagamento"]),
                                        "tipo": str(row_ed["Tipo"]),
                                        "categoria": str(row_ed["Categoria"]),
                                        "subcategoria": str(row_ed["Subcategoria"]),
                                        "conta_cartao": str(row_ed["Conta_Cartao"]),
                                        "descricao": str(row_ed["Descricao"]),
                                        "valor": float(row_ed["Valor"]),
                                        "status": str(row_ed["Status"])
                                    }).eq("id", str(row_ed["ID"])).execute()
                                    mudancas += 1
                            st.success(f"✅ Salvo!")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar: {e}")
                with c_op2:
                    if st.button("✅ Marcar como Pago", use_container_width=True) and ids_selecionados:
                        supabase.table("lancamentos").update({"status": "Pago"}).in_("id", ids_selecionados).execute()
                        st.rerun()
                with c_op3:
                    if st.button("⏳ Marcar como Pendente", use_container_width=True) and ids_selecionados:
                        supabase.table("lancamentos").update({"status": "Pendente"}).in_("id", ids_selecionados).execute()
                        st.rerun()
                with c_op4:
                    if st.button("🗑️ Apagar Selecionados", use_container_width=True) and ids_selecionados:
                        st.session_state.confirmar_delecao = ids_selecionados
                        st.rerun()
        else:
            st.info("Nenhum lançamento encontrado para gerenciar. Por favor, adicione novos dados.")

# ========================================================
# 8. SUPER CENTRAL DE CADASTROS
# ========================================================
with aba_cadastros:
    st.markdown("### ⚙️ Central de Cadastros e Configurações")
    
    col_dict = {"Contas e Cartões": "Cartao", "Categorias Gerais": "Categoria", "Subcategorias": "Subcategoria", "Responsáveis": "Responsavel", "Fornecedores / Origens": "Origem_Destino"}
    tipo_cadastro = st.selectbox("Selecione a lista para gerenciar:", list(col_dict.keys()))
    col_db = col_dict[tipo_cadastro]
    
    if col_db == "Cartao":
        with st.container(border=True):
            st.markdown("#### Adicionar Cartão / Conta")
            c1, c2, c3 = st.columns(3)
            with c1: banco_cartao = st.selectbox("Banco", LISTA_BANC_BASE)
            with c2: final_cartao = st.text_input("Nome/Final (Ex: Final 1234, Conta Empresa)")
            with c3: dia_vencimento = st.number_input("Dia de Vencimento da Fatura (1 para contas)", 1, 31, 10)
            if st.button("Salvar Cartão", type="primary") and final_cartao:
                auto_salvar_cadastro("Cartao", f"{banco_cartao} - {final_cartao} (Venc: dia {dia_vencimento})")
                st.rerun()
                
        st.markdown("#### Seus Cartões e Contas Registados")
        if not df_cartoes.empty:
            df_cv = df_cartoes[["ID", "Conta_Cartao", "Categoria", "Valor"]].rename(columns={"Conta_Cartao": "Conta / Cartão", "Categoria": "Banco", "Valor": "Vencimento"})
            st.dataframe(df_cv.drop(columns=["ID"]), use_container_width=True, hide_index=True)
            cartao_apagar = st.selectbox("Selecione para remover:", df_cv["Conta / Cartão"].tolist())
            if st.button("Remover Selecionado"):
                id_rem = df_cartoes[df_cartoes["Conta_Cartao"] == cartao_apagar]["ID"].iloc[0]
                supabase.table("lancamentos").delete().eq("id", id_rem).execute()
                st.rerun()
    else:
        if col_db == "Categoria": lista_padrao = LISTA_CAT_DESP + LISTA_CAT_REC + LISTA_CAT_INV
        elif col_db == "Responsavel": lista_padrao = LISTA_RESP_BASE
        elif col_db == "Subcategoria": lista_padrao = SUBCATS_BASE
        else: lista_padrao = LISTA_ORIG_BASE
        
        opcoes_atuais = obter_opcoes(col_db, lista_padrao)
        
        c_cad1, c_cad2 = st.columns(2)
        with c_cad1:
            with st.container(border=True):
                st.markdown(f"#### ➕ Forçar Novo Cadastro")
                
                cat_vinculo = ""
                if col_db == "Subcategoria":
                    cat_vinculo = st.selectbox("Pertence a qual Categoria?", obter_opcoes("Categoria", LISTA_CAT_DESP + LISTA_CAT_REC + LISTA_CAT_INV))
                
                novo_item = st.text_input(f"Digitar novo(a) {tipo_cadastro}")
                
                if st.button("Salvar na Lista") and novo_item:
                    auto_salvar_cadastro(col_db, novo_item, cat_vinculo)
                    st.success("Salvo!")
                    time.sleep(1)
                    st.rerun()
                    
        with c_cad2:
            with st.container(border=True):
                st.markdown(f"#### 🗑️ Ocultar do Formulário")
                if opcoes_atuais:
                    item_apagar = st.selectbox("Selecione para colocar na Lista Negra:", opcoes_atuais)
                    if st.button("Esconder Item"):
                        supabase.table("lancamentos").insert({"user_email": st.session_state.user_email, "data_compra": datetime.now().strftime("%Y-%m-%d"), "competencia": datetime.now().strftime("%Y-%m"), "mes_pagamento": datetime.now().strftime("%Y-%m"), "tipo": "Config_Excluida", "categoria": col_db, "subcategoria": item_apagar, "responsavel": st.session_state.user_nome, "origem_destino": "", "conta_cartao": "", "valor": 0.0, "descricao": "Oculto", "parcela": "-", "status": "Config"}).execute()
                        st.success("Item Ocultado!")
                        time.sleep(1)
                        st.rerun()

# ========================================================
# 9. ASSISTENTE IA
# ========================================================
with aba_assistente:
    st.markdown("### 🤖 Cérebro Digital")
    if modelo_ia and st.session_state.user_email:
        prompt = st.chat_input("Pergunte sobre seus dados...")
        if prompt:
            with st.chat_message("user"): st.markdown(prompt)
            try:
                colunas_ia = ["Data", "Mes_Pagamento", "Tipo", "Categoria", "Conta_Cartao", "Valor", "Status", "Responsavel"]
                hist_txt = df[colunas_ia].to_string() if not df.empty else "Vazio."
                res = modelo_ia.generate_content(f"Aja como um assistente financeiro. Dados:\n{hist_txt}\nPergunta: {prompt}")
                with st.chat_message("assistant"): st.markdown(res.text)
            except Exception as e: st.error(f"Erro IA: {e}")
