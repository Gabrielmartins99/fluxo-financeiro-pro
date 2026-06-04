import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import json
from supabase import create_client, Client
import google.generativeai as genai

# ========================================================
# 1. CREDENCIAIS DE BANCO DE DADOS E INTELIGÊNCIA ARTIFICIAL
# ========================================================
SUPABASE_URL = "https://tlrrauzylknuatajzniu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRscnJhdXp5bGtudWF0YWp6bml1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA1MDE5ODMsImV4cCI6MjA5NjA3Nzk4M30.WiTNExA0hJY0AmDY794F7O0ft2SngctNoWQ_LBwyGDk"

# 🔑 COLE A SUA CHAVE DO GOOGLE AI STUDIO AQUI DENTRO DAS ASPAS:
GEMINI_API_KEY = "COLE_SUA_CHAVE_COPIADA_AQUI" 

@st.cache_resource
def init_connection():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_connection()

# Configuração do Cérebro da IA
if GEMINI_API_KEY != "COLE_SUA_CHAVE_COPIADA_AQUI":
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
    </style>
""", unsafe_allow_html=True)

# ========================================================
# 3. SISTEMA DE AUTENTICAÇÃO
# ========================================================
if "user_email" not in st.session_state:
    st.session_state.user_email = None

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
# 4. FUNÇÕES BASE
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
    except Exception as e:
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

# ========================================================
# 5. HEADER DO USUÁRIO LOGADO E NAVEGAÇÃO
# ========================================================
c_head1, c_head2 = st.columns([4, 1])
with c_head1: st.markdown("<h2 class='title-gradient'>Fluxo Financeiro PRO</h2>", unsafe_allow_html=True)
with c_head2:
    st.write(f"👤 {st.session_state.user_email.split('@')[0]}")
    if st.button("Sair (Logout)"):
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
        st.subheader("Registrar Movimentação Avançada")
        col1, col2, col3 = st.columns(3)
        with col1:
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            data_compra = st.date_input("Data da Compra")
            valor_total = st.number_input("Valor Total (R$)", min_value=0.0)
            st.markdown("---")
            modo_lancamento = st.radio("Como é este lançamento?", ["Único (À vista)", "Parcelado", "Assinatura Mensal (Recorrente)"])
        with col2:
            categoria = st.selectbox("Categoria", obter_opcoes("Categoria", LISTA_CATEGORIAS))
            conta_cartao = st.selectbox("Conta / Cartão", obter_opcoes("Conta_Cartao", LISTA_BANCOS))
            descricao = st.text_input("Descrição (Ex: Netflix, iFood)")
            st.markdown("---")
            if modo_lancamento == "Parcelado":
                parcelas = st.number_input("Número de Parcelas", min_value=2, max_value=120, value=2)
            elif modo_lancamento == "Assinatura Mensal (Recorrente)":
                parcelas = st.number_input("Projetar por quantos meses?", min_value=2, max_value=60, value=12)
            else:
                parcelas = 1
        with col3:
            responsavel = st.selectbox("Dono do Gasto (Responsável)", obter_opcoes("Responsavel", ["Gabriel", "Tainá", "Família", "Empresa"]))
            mes_fatura = st.date_input("Mês da 1ª Fatura/Cobrança")

        if st.button("💾 Lançar no Sistema", type="primary") and valor_total > 0:
            novas_linhas = []
            if modo_lancamento == "Parcelado":
                valor_por_mes = valor_total / parcelas
                info_parcela = lambda i: f"{i+1}/{parcelas}"
            elif modo_lancamento == "Assinatura Mensal (Recorrente)":
                valor_por_mes = valor_total 
                info_parcela = lambda i: "Recorrente"
            else:
                valor_por_mes = valor_total
                info_parcela = lambda i: "À vista"

            for i in range(parcelas):
                m = mes_fatura.month - 1 + i
                y = mes_fatura.year + (m // 12)
                comp = f"{y}-{(m % 12) + 1:02d}"
                novas_linhas.append({
                    "user_email": st.session_state.user_email, "data_compra": data_compra.strftime("%Y-%m-%d"),
                    "competencia": comp, "tipo": tipo, "categoria": categoria, "subcategoria": "Geral",
                    "conta_cartao": conta_cartao, "valor": float(round(valor_por_mes, 2)),
                    "descricao": descricao, "parcela": info_parcela(i), "responsavel": responsavel, 
                    "status": "Pago" if i == 0 else "Pendente"
                })
            try:
                supabase.table("lancamentos").insert(novas_linhas).execute()
                st.success("✅ Lançamento processado com sucesso!")
                time.sleep(1.5)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar na nuvem: {e}")

    with aba_importar:
        st.subheader("Integração Inteligente de Faturas")
        st.info("**💡 Dica:** Exporte sua fatura em CSV/Excel pelo App do banco e anexe abaixo.")
        banco_selecionado = st.selectbox("Selecione o banco de origem da fatura", ["Nubank", "Inter", "Itaú", "Outro"])
        arquivo = st.file_uploader("Anexe o arquivo da fatura aqui", type=["csv", "xlsx", "xls"])
        
        if arquivo is not None:
            try:
                if arquivo.name.endswith('.csv'):
                    df_fatura = pd.read_csv(arquivo, sep=None, engine='python') 
                else:
                    df_fatura = pd.read_excel(arquivo)
                
                if "Categoria_Sistema" not in df_fatura.columns: df_fatura["Categoria_Sistema"] = "Outros"
                if "Tipo_Sistema" not in df_fatura.columns: df_fatura["Tipo_Sistema"] = "Despesa"
                    
                st.success("✅ Arquivo lido. Mapeie as colunas abaixo:")
                c1, c2, c3 = st.columns(3)
                col_data = c1.selectbox("Qual coluna contém a Data?", df_fatura.columns)
                col_desc = c2.selectbox("Qual coluna contém a Descrição?", df_fatura.columns)
                col_valor = c3.selectbox("Qual coluna contém o Valor?", df_fatura.columns)
                
                df_editado = st.data_editor(df_fatura, num_rows="dynamic", use_container_width=True)
                
                if st.button("🚀 Confirmar e Salvar Lançamentos", type="primary"):
                    novas_linhas = []
                    mes_atual = datetime.now().strftime("%Y-%m")
                    for index, row in df_editado.iterrows():
                        try:
                            val_str = str(row[col_valor]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                            val = float(val_str)
                            if val == 0: continue
                        except: val = 0.0
                        novas_linhas.append({
                            "user_email": st.session_state.user_email, "data_compra": str(row[col_data])[:10],
                            "competencia": mes_atual, "tipo": row.get("Tipo_Sistema", "Despesa"),
                            "categoria": row.get("Categoria_Sistema", "Outros"), "subcategoria": "Importado",
                            "conta_cartao": banco_selecionado, "valor": abs(val),
                            "descricao": str(row[col_desc]), "parcela": "Fatura",
                            "responsavel": "Eu", "status": "Pago"
                        })
                    if novas_linhas:
                        supabase.table("lancamentos").insert(novas_linhas).execute()
                        st.success(f"✅ {len(novas_linhas)} lançamentos importados para a nuvem!")
                        time.sleep(2)
                        st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar arquivo: {e}")

# ========================================================
# 8. ABA ASSISTENTE IA (O CÉREBRO DIGITAL ATIVO)
# ========================================================
with aba_assistente:
    st.markdown("### 🤖 Cérebro Digital - O seu Assistente Pessoal")
    
    if not modelo_ia:
        st.warning("⚠️ O Cérebro ainda está dormindo. Cole a sua chave da API do Google na Seção 1 do código para acordá-lo!")
    else:
        # Inicializa a memória da conversa
        if "mensagens_chat" not in st.session_state:
            st.session_state.mensagens_chat = [{"role": "assistant", "content": "Olá! Eu sou o Assistente IA do Fluxo Financeiro PRO. Pode conversar comigo ou me pedir para registrar um gasto (ex: 'Gastei 50 no iFood no Nubank hoje')."}]

        # Renderiza a conversa
        for msg in st.session_state.mensagens_chat:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Onde o usuário digita
        prompt = st.chat_input("Digite sua mensagem aqui...")
        
        if prompt:
            st.session_state.mensagens_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("Processando..."):
                    try:
                        # O Prompt de Comando secreto que a IA recebe para agir como sistema
                        instrucao_sistema = f"""
                        Você é o assistente financeiro do aplicativo 'Fluxo Financeiro PRO'.
                        O usuário disse: "{prompt}"
                        
                        Se for apenas uma conversa, dúvida ou conselho financeiro, responda normalmente, de forma amigável e curta.
                        
                        Se o usuário estiver relatando um GASTO ou uma RECEITA, você deve responder amigavelmente confirmando que registrou E, no final da sua resposta, incluir EXATAMENTE este bloco de código JSON abaixo preenchido com os dados que você extraiu da frase do usuário (use as categorias: Alimentação, Transporte, Moradia, Salário, Lazer, Saúde, Educação, Investimentos, Outros):
                        
                        ```json
                        {{
                            "acao": "registrar",
                            "tipo": "Despesa",
                            "valor": 0.00,
                            "descricao": "",
                            "categoria": "",
                            "conta": ""
                        }}
                        ```
                        """
                        
                        # Chama a API do Google Gemini
                        resposta = modelo_ia.generate_content(instrucao_sistema)
                        texto_resposta = resposta.text
                        
                        # Limpa a tela para não mostrar o código JSON feio pro usuário
                        texto_limpo = texto_resposta.split("```json")[0].strip()
                        st.markdown(texto_limpo)
                        st.session_state.mensagens_chat.append({"role": "assistant", "content": texto_limpo})
                        
                        # Se a IA detectou um gasto e gerou o JSON, o sistema intercepta e salva no Supabase!
                        if "```json" in texto_resposta:
                            bloco_json = texto_resposta.split("```json")[1].split("```")[0].strip()
                            dados_ia = json.loads(bloco_json)
                            
                            if dados_ia.get("acao") == "registrar":
                                mes_atual = datetime.now().strftime("%Y-%m")
                                data_hoje = datetime.now().strftime("%Y-%m-%d")
                                
                                nova_linha = {
                                    "user_email": st.session_state.user_email,
                                    "data_compra": data_hoje,
                                    "competencia": mes_atual,
                                    "tipo": dados_ia.get("tipo", "Despesa"),
                                    "categoria": dados_ia.get("categoria", "Outros"),
                                    "subcategoria": "Lançado via IA",
                                    "conta_cartao": dados_ia.get("conta", "Conta Automática"),
                                    "valor": float(dados_ia.get("valor", 0.0)),
                                    "descricao": dados_ia.get("descricao", "Lançamento via Assistente"),
                                    "parcela": "À vista",
                                    "responsavel": "Eu",
                                    "status": "Pago"
                                }
                                supabase.table("lancamentos").insert(nova_linha).execute()
                                st.toast("✅ Mágica Feita! A IA gravou o dado diretamente no banco.")
                                
                    except Exception as e:
                        st.error(f"Erro de comunicação com o Cérebro IA: {e}")

# ========================================================
# 9. ABA OPEN FINANCE
# ========================================================
with aba_openfinance:
    st.subheader("🔌 Hub de Integração Aberta")
    st.info("A infraestrutura do banco de dados na nuvem foi configurada com sucesso. A conexão via Hub Integrador será iniciada na próxima etapa.")
