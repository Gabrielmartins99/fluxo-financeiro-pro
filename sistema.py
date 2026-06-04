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
# 1. CREDENCIAIS DE BANCO DE DADOS, IA E OPEN FINANCE
# ========================================================
SUPABASE_URL = "https://tlrrauzylknuatajzniu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRscnJhdXp5bGtudWF0YWp6bml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1MDE5ODMsImV4cCI6MjA5NjA3Nzk4M30.WiTNExA0hJY0AmDY794F7O0ft2SngctNoWQ_LBwyGDk"

# Puxa as chaves do cofre de forma segura
try:
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
    PLUGGY_CLIENT_ID = st.secrets.get("PLUGGY_CLIENT_ID", "")
    PLUGGY_CLIENT_SECRET = st.secrets.get("PLUGGY_CLIENT_SECRET", "")
except:
    GEMINI_API_KEY = ""
    PLUGGY_CLIENT_ID = ""
    PLUGGY_CLIENT_SECRET = ""

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
        .pluggy-card { background: white; border: 1px solid #E2E8F0; border-radius: 10px; padding: 15px; text-align: center; font-weight: 600; color: #4F46E5;}
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. SISTEMA DE AUTENTICAÇÃO COM COOKIES
# ========================================================
if "user_email" not in st.session_state:
    st.session_state.user_email = None

cookie_manager = stx.CookieManager(key="meu_gerenciador_cookies")

if st.session_state.user_email is None:
    cookie_email = cookie_manager.get(cookie="user_email")
    if cookie_email:
        st.session_state.user_email = cookie_email

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
                    except Exception as e:
                        st.error("E-mail ou senha incorretos. Tente novamente.")
                        
            with aba_registro:
                email_reg = st.text_input("Melhor E-mail", key="reg_email")
                senha_reg = st.text_input("Crie uma Senha Forte", type="password", key="reg_senha")
                if st.button("Garantir Meu Acesso", type="primary", use_container_width=True):
                    try:
                        res = supabase.auth.sign_up({"email": email_reg, "password": senha_reg})
                        st.success("✅ Conta criada com sucesso! Pode fazer o seu login agora mesmo na aba ao lado.")
                    except Exception as e:
                        st.error("Erro ao criar conta. Verifique os dados inseridos.")
    st.stop()

# ========================================================
# 4. FUNÇÕES BASE E CONEXÃO PLUGGY
# ========================================================
def carregar_dados():
    try:
        response = supabase.table("lancamentos").select("*").eq("user_email", st.session_state.user_email).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.rename(columns={
                "data_compra": "Data", "competencia": "Competencia", "tipo": "Tipo", "categoria": "Categoria",
                "subcategoria": "Subcategoria", "conta_cartao": "Conta_Cartao", "valor": "Valor",
                "descricao": "Descricao", "parcela": "Parcela", "responsavel": "Responsavel", "status": "Status"
            })
            df["Valor"] = pd.to_numeric(df["Valor"]).fillna(0.0)
            return df
    except:
        pass
    return pd.DataFrame(columns=["ID", "Data", "Competencia", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status"])

df = carregar_dados()

def obter_opcoes(coluna, lista_base):
    if not df.empty and coluna in df.columns:
        existentes = df[coluna].dropna().astype(str).unique().tolist()
        return sorted(list(set(lista_base + [x.strip() for x in existentes if x.strip() not in ["", "-", "None"]])))
    return sorted(lista_base)

LISTA_BANCOS = ["Nubank", "Inter", "Itaú", "Bradesco", "Banco do Brasil", "Pix/Dinheiro"]
LISTA_CATEGORIAS = ["Alimentação", "Transporte", "Moradia", "Salário", "Lazer", "Saúde", "Educação", "Investimentos", "Outros"]

# Motor da Pluggy (Gera a API Key temporária e lista os bancos)
def obter_token_pluggy():
    if not PLUGGY_CLIENT_ID or not PLUGGY_CLIENT_SECRET:
        return None
    url = "https://api.pluggy.ai/auth"
    payload = {"clientId": PLUGGY_CLIENT_ID, "clientSecret": PLUGGY_CLIENT_SECRET}
    headers = {"accept": "application/json", "content-type": "application/json"}
    try:
        res = requests.post(url, json=payload, headers=headers)
        if res.status_code == 200:
            return res.json().get("apiKey")
    except:
        pass
    return None

def listar_bancos_pluggy(api_key):
    url = "https://api.pluggy.ai/connectors?countries=BR&types=PERSONAL_BANK"
    headers = {"accept": "application/json", "X-API-KEY": api_key}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            return res.json().get("results", [])
    except:
        pass
    return []

# ========================================================
# 5. HEADER DO USUÁRIO LOGADO
# ========================================================
c_head1, c_head2 = st.columns([4, 1])
with c_head1: st.markdown("<h2 class='title-gradient'>Fluxo Financeiro PRO</h2>", unsafe_allow_html=True)
with c_head2:
    st.write(f"👤 {st.session_state.user_email.split('@')[0]}")
    if st.button("Sair (Logout)"):
        cookie_manager.delete("user_email")
        st.session_state.user_email = None
        supabase.auth.sign_out()
        st.rerun()

aba_dashboard, aba_lancamentos, aba_assistente, aba_openfinance = st.tabs(["📊 Dashboard", "📝 Lançamentos", "🤖 Assistente IA", "🔌 Open Finance"])

# ========================================================
# 6. ABA DASHBOARD
# ========================================================
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        dash_mensal, dash_anual = st.tabs(["📅 Visão Mensal", "📈 Visão Anual (Evolução)"])
        
        with dash_mensal:
            col_filtro1, col_filtro2 = st.columns(2)
            with col_filtro1:
                meses_disponiveis = sorted(df["Competencia"].unique(), reverse=True)
                mes_selecionado = st.selectbox("Selecione o Mês / Fatura", ["Ver Tudo"] + meses_disponiveis)
            
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
                col_graf1, col_graf2 = st.columns(2)
                with col_graf1:
                    fig1 = px.pie(df_dash[df_dash["Tipo"] == "Despesa"], values="Valor", names="Categoria", title="Distribuição por Categoria", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    st.plotly_chart(fig1, use_container_width=True)
                with col_graf2:
                    df_top = df_dash[df_dash["Tipo"] == "Despesa"].groupby("Descricao")["Valor"].sum().reset_index().sort_values("Valor", ascending=False).head(5)
                    fig2 = px.bar(df_top, x="Valor", y="Descricao", orientation='h', title="Top 5 Maiores Despesas", text_auto='.2s', color="Valor", color_continuous_scale="Reds")
                    fig2.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig2, use_container_width=True)
        
        with dash_anual:
            st.markdown("### 📈 Evolução do Patrimônio e Análise Profunda")
            df_evolucao = df.groupby(["Competencia", "Tipo"])["Valor"].sum().reset_index()
            fig_evo = px.bar(df_evolucao, x="Competencia", y="Valor", color="Tipo", barmode="group", title="Receitas vs Despesas ao Longo do Tempo", color_discrete_map={"Receita": "#16A34A", "Despesa": "#DC2626"})
            st.plotly_chart(fig_evo, use_container_width=True)
            
            st.markdown("---")
            col_anual1, col_anual2 = st.columns(2)
            with col_anual1:
                df_banco = df[df["Tipo"] == "Despesa"].groupby("Conta_Cartao")["Valor"].sum().reset_index()
                fig_banco = px.pie(df_banco, values="Valor", names="Conta_Cartao", title="Despesas por Conta/Cartão", hole=0.3, color_discrete_sequence=px.colors.sequential.Blues_r)
                st.plotly_chart(fig_banco, use_container_width=True)
            with col_anual2:
                df_resp = df[df["Tipo"] == "Despesa"].groupby("Responsavel")["Valor"].sum().reset_index()
                fig_resp = px.pie(df_resp, values="Valor", names="Responsavel", title="Gastos por Responsável", hole=0.3, color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig_resp, use_container_width=True)
    else:
        st.info("O Dashboard está aguardando lançamentos.")

# ========================================================
# 7. ABA LANÇAMENTOS
# ========================================================
with aba_lancamentos:
    aba_manual, aba_importar = st.tabs(["✍️ Lançamento Manual", "📥 Importar Fatura de Cartão"])
    
    with aba_manual:
        st.subheader("Registrar Movimentação")
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            data_compra = st.date_input("Data da Compra")
            valor_total = st.number_input("Valor Total (R$)", min_value=0.0)
            modo_lancamento = st.radio("Lançamento:", ["Único", "Parcelado", "Assinatura"])
        with col2:
            categoria = st.selectbox("Categoria", obter_opcoes("Categoria", LISTA_CATEGORIAS))
            conta_cartao = st.selectbox("Conta / Cartão", obter_opcoes("Conta_Cartao", LISTA_BANCOS))
            descricao = st.text_input("Descrição")
            parcelas = st.number_input("Parcelas/Meses", min_value=1, value=1) if modo_lancamento != "Único" else 1
        with col3:
            responsavel = st.selectbox("Responsável", obter_opcoes("Responsavel", ["Gabriel", "Tainá", "Família"]))
            mes_fatura = st.date_input("Mês da Cobrança")

        if st.button("💾 Lançar no Sistema", type="primary") and valor_total > 0:
            novas_linhas = []
            valor_por_mes = valor_total / parcelas if modo_lancamento == "Parcelado" else valor_total
            for i in range(parcelas):
                m = mes_fatura.month - 1 + i
                y = mes_fatura.year + (m // 12)
                comp = f"{y}-{(m % 12) + 1:02d}"
                novas_linhas.append({
                    "user_email": st.session_state.user_email, "data_compra": data_compra.strftime("%Y-%m-%d"),
                    "competencia": comp, "tipo": tipo, "categoria": categoria, "subcategoria": "Geral",
                    "conta_cartao": conta_cartao, "valor": float(round(valor_por_mes, 2)),
                    "descricao": descricao, "parcela": f"{i+1}/{parcelas}" if modo_lancamento == "Parcelado" else "Recorrente" if modo_lancamento == "Assinatura" else "À vista", 
                    "responsavel": responsavel, "status": "Pago" if i == 0 else "Pendente"
                })
            supabase.table("lancamentos").insert(novas_linhas).execute()
            st.success("Lançamento processado!")
            time.sleep(1)
            st.rerun()

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
                    try:
                        val = float(str(row[col_valor]).replace('R$', '').replace('.', '').replace(',', '.').strip())
                        if val == 0: continue
                    except: val = 0.0
                    novas_linhas.append({
                        "user_email": st.session_state.user_email, "data_compra": str(row[col_data])[:10],
                        "competencia": datetime.now().strftime("%Y-%m"), "tipo": row.get("Tipo_Sistema", "Despesa"),
                        "categoria": row.get("Categoria_Sistema", "Outros"), "conta_cartao": "Importado",
                        "valor": abs(val), "descricao": str(row[col_desc]), "parcela": "Fatura",
                        "responsavel": "Eu", "status": "Pago"
                    })
                if novas_linhas:
                    supabase.table("lancamentos").insert(novas_linhas).execute()
                    st.success("Importado!")
                    time.sleep(1)
                    st.rerun()

# ========================================================
# 8. ABA ASSISTENTE IA (CÓDIGO PROTEGIDO CONTRA CORTES)
# ========================================================
with aba_assistente:
    st.markdown("### 🤖 Cérebro Digital")
    if modelo_ia:
        if "mensagens_chat" not in st.session_state:
            st.session_state.mensagens_chat = [{"role": "assistant", "content": "Olá! Me peça para registrar um gasto!"}]
        for msg in st.session_state.mensagens_chat:
            with st.chat_message(msg["role"]): 
                st.markdown(msg["content"])
        
        prompt = st.chat_input("Digite sua mensagem...")
        if prompt:
            st.session_state.mensagens_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"): 
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Processando..."):
                    try:
                        resposta = modelo_ia.generate_content(f'O usuário disse: "{prompt}". Se for um gasto, gere um JSON no final com acao: registrar, tipo, valor, descricao, categoria, conta.')
                        texto_resposta = resposta.text
                        
                        texto_limpo = texto_resposta.split("```json")[0].strip()
                        st.markdown(texto_limpo)
                        st.session_state.mensagens_chat.append({"role": "assistant", "content": texto_limpo})
                        
                        if "```json" in texto_resposta:
                            bloco_bruto = texto_resposta.split("```json")[1]
                            bloco_json = bloco_bruto.split("```")[0].strip()
                            dados_ia = json.loads(bloco_json)
                            
                            if dados_ia.get("acao") == "registrar":
                                nova_linha = {
                                    "user_email": st.session_state.user_email, 
                                    "data_compra": datetime.now().strftime("%Y-%m-%d"), 
                                    "competencia": datetime.now().strftime("%Y-%m"), 
                                    "tipo": dados_ia.get("tipo", "Despesa"), 
                                    "categoria": dados_ia.get("categoria", "Outros"), 
                                    "conta_cartao": dados_ia.get("conta", "IA"), 
                                    "valor": float(dados_ia.get("valor", 0.0)), 
                                    "descricao": dados_ia.get("descricao", "Assistente"), 
                                    "parcela": "À vista", 
                                    "responsavel": "Eu", 
                                    "status": "Pago"
                                }
                                supabase.table("lancamentos").insert(nova_linha).execute()
                                st.toast("✅ Registrado pela IA!")
                    except Exception as e:
                        st.error(f"Erro de IA: {e}")

# ========================================================
# 9. ABA OPEN FINANCE (A CONEXÃO REAL)
# ========================================================
with aba_openfinance:
    st.subheader("🔌 Hub de Integração Bancária")
    st.write("Conecte suas contas bancárias para sincronização automática dos seus extratos.")
    st.info("**Ambiente Seguro:** Credenciais criptografadas de ponta a ponta. Autorizado pelo Banco Central.")

    if not PLUGGY_CLIENT_ID:
        st.warning("⚠️ Suas credenciais da Pluggy ainda não foram lidas pelo sistema. Verifique o cofre (Secrets).")
    else:
        if st.button("📡 Autenticar com os Servidores da Pluggy", type="primary"):
            with st.spinner("Negociando chaves de segurança com a Pluggy..."):
                chave_api = obter_token_pluggy()
                
                if chave_api:
                    st.success("✅ Conexão estabelecida! Listando instituições suportadas...")
                    bancos_oficiais = listar_bancos_pluggy(chave_api)
                    
                    if bancos_oficiais:
                        cols = st.columns(4)
                        for idx, banco in enumerate(bancos_oficiais[:8]): 
                            with cols[idx % 4]:
                                st.markdown(f'<div class="pluggy-card">{banco["name"]}</div>', unsafe_allow_html=True)
                                st.write("")
                        
                        st.markdown("---")
                        st.write("**Aviso:** A renderização completa do Widget seguro de digitação de senha requer a inclusão do SDK Javascript da Pluggy no Streamlit.")
                    else:
                        st.warning("Não foi possível listar os bancos no momento.")
                else:
                    st.error("Falha na autenticação. Verifique suas credenciais no cofre.")
