import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
import uuid
import time

# ---------------------------------------------------------
# PASSO 1: Configuração Inicial e Engenharia de Estilo Cyber-Minimalist
# ---------------------------------------------------------
st.set_page_config(page_title="Fluxo Financeiro PRO", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            background-color: #F8FAFC !important;
            color: #0F172A !important;
        }
        
        h1 {
            font-weight: 800 !important;
            letter-spacing: -2px !important;
            background: linear-gradient(90deg, #0284C7 0%, #4F46E5 50%, #7C3AED 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding-bottom: 20px;
        }
        
        h2, h3, h4, h5, h6 {
            color: #0F172A !important;
            font-weight: 700 !important;
        }
        
        label, div[data-testid="stWidgetLabel"] p, .stMarkdown p {
            color: #475569 !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            font-size: 0.85rem !important;
        }
        
        div[data-baseweb="input"], div[data-baseweb="select"], .stSelectbox div, .stTextInput div, .stMultiSelect div {
            background-color: #FFFFFF !important;
            border: 1px solid rgba(79, 70, 229, 0.2) !important;
            border-radius: 10px !important;
            color: #0F172A !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02) !important;
        }
        
        input, select, textarea, div[data-baseweb="select"] * {
            color: #0F172A !important;
            background-color: #FFFFFF !important;
        }
        
        div[data-baseweb="popover"], div[role="listbox"], li[data-baseweb="option"] {
            background-color: #FFFFFF !important;
            color: #0F172A !important;
        }
        li[data-baseweb="option"]:hover {
            background-color: #F1F5F9 !important;
            color: #4F46E5 !important;
        }
        
        button[data-baseweb="tab"] {
            color: #94A3B8 !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            border-bottom: 3px solid transparent !important;
            transition: all 0.2s ease;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: #4F46E5 !important;
            border-bottom: 3px solid #4F46E5 !important;
        }
        
        button, .stButton button, button[data-testid="baseButton-secondary"] {
            background-color: #FFFFFF !important;
            border: 1px solid #4F46E5 !important;
            border-radius: 10px !important;
            padding: 10px 26px !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.05) !important;
        }
        button p, button span, button div {
            color: #4F46E5 !important;
            font-weight: 700 !important;
        }
        button:hover, .stButton button:hover {
            background: linear-gradient(90deg, #4F46E5 0%, #7C3AED 100%) !important;
            border-color: transparent !important;
            box-shadow: 0 4px 20px rgba(79, 70, 229, 0.4) !important;
        }
        button:hover p, button:hover span {
            color: #FFFFFF !important;
        }
        
        div.stButton > button[kind="primary"] {
            background: linear-gradient(90deg, #0284C7 0%, #4F46E5 100%) !important;
            border: none !important;
            box-shadow: 0 4px 20px rgba(2, 132, 199, 0.25) !important;
        }
        div.stButton > button[kind="primary"] p, div.stButton > button[kind="primary"] span {
            color: #FFFFFF !important;
            font-weight: 800 !important;
        }
        div.stButton > button[kind="primary"]:hover {
            box-shadow: 0 4px 25px rgba(2, 132, 199, 0.5) !important;
            transform: translateY(-1px);
        }
        
        .executive-box {
            background-color: #FFFFFF;
            border: 1px solid rgba(15, 23, 42, 0.06);
            border-radius: 16px;
            padding: 26px;
            box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
            transition: transform 0.2s ease;
        }
        
        .step-box {
            background-color: #FFFFFF;
            border: 1px solid rgba(79, 70, 229, 0.1);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.01);
        }
        .step-num {
            background-color: #4F46E5;
            color: white;
            border-radius: 50%;
            width: 28px;
            height: 28px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 10px;
        }

        .bank-card {
            background-color: #FFFFFF;
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
            transition: all 0.2s ease;
        }
        .bank-card:hover {
            border-color: #4F46E5;
            transform: translateY(-2px);
        }
        
        .secure-widget {
            background-color: #FFFFFF;
            color: #0F172A;
            border-radius: 16px;
            padding: 30px;
            border: 1px solid rgba(79, 70, 229, 0.2);
            box-shadow: 0 20px 50px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

ARQUIVO_DADOS = "dados_financeiros.csv"
COLUNAS_PADRAO = ["ID", "Data", "Tipo", "Categoria", "Subcategoria", "Conta_Cartao", "Valor", "Descricao", "Parcela", "Responsavel", "Status"]

if "of_step" not in st.session_state: st.session_state.of_step = "inicio"
if "of_banco" not in st.session_state: st.session_state.of_banco = ""

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        try:
            df = pd.read_csv(ARQUIVO_DADOS, dtype=str) 
            for col in COLUNAS_PADRAO:
                if col not in df.columns: df[col] = "-"
            if "Responsavel" in df.columns:
                df["Responsavel"] = df["Responsavel"].replace("Gabriel (Eu)", "Gabriel")
            df["Valor"] = pd.to_numeric(df["Valor"].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
            df["Descricao"] = df["Descricao"].fillna("Sem descrição")
            df["ID"] = df["ID"].apply(lambda x: str(uuid.uuid4()) if pd.isna(x) or str(x).strip() in ["", "-"] else x)
            return df.dropna(how="all")
        except: pass
    return pd.DataFrame(columns=COLUNAS_PADRAO)

df = carregar_dados()

def obter_opcoes(coluna, lista_base):
    if not df.empty and coluna in df.columns:
        existentes = df[coluna].dropna().astype(str).unique().tolist()
        return sorted(list(set(lista_base + [x.strip() for x in existentes if x.strip() not in ["", "-"]])))
    return sorted(lista_base)

aba_dashboard, aba_lancamentos, aba_openfinance, aba_gerenciar, aba_importar = st.tabs([
    "📊 Dashboard Financeiro", "📝 Novos Lançamentos", "🔌 Conexão Open Finance", "⚙️ Gestor de Dados", "📥 Importação de Planilhas"
])

# ---------------------------------------------------------
# ABA DASHBOARD
# ---------------------------------------------------------
with aba_dashboard:
    if not df.empty and df["Valor"].sum() > 0:
        df["Data_Limpa"] = pd.to_datetime(df["Data"], errors='coerce')
        df["Mes_Ano"] = df["Data_Limpa"].dt.to_period("M").astype(str)
        
        col_filtro1, col_filtro2 = st.columns(2)
        with col_filtro1:
            mes_selecionado = st.selectbox("📅 Janela Temporal (Mês)", ["Ver Tudo"] + sorted(df["Mes_Ano"].unique(), reverse=True))
        with col_filtro2:
            lista_resps = sorted(df["Responsavel"].dropna().unique().tolist())
            resps_selected = st.multiselect("👤 Filtrar por Responsável(is)", options=lista_resps, default=lista_resps)
        
        df_dash = df[df["Mes_Ano"] == mes_selecionado] if mes_selecionado != "Ver Tudo" else df.copy()
        if resps_selected:
            df_dash = df_dash[df_dash["Responsavel"].isin(resps_selected)]
        
        t_rec = df_dash[(df_dash["Tipo"] == "Receita")]["Valor"].sum()
        t_desp = df_dash[(df_dash["Tipo"] == "Despesa")]["Valor"].sum()
        saldo_liquido = t_rec - t_desp
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="executive-box" style="border-top: 4px solid #0284C7;"><div class="term-label">Saldo Líquido Filtrado</div><div class="term-amount" style="color:#0284C7;">R$ {saldo_liquido:,.2f}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="executive-box" style="border-top: 4px solid #16A34A;"><div class="term-label">Entradas Líquidas (+)</div><div class="term-amount" style="color:#16A34A;">R$ {t_rec:,.2f}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="executive-box" style="border-top: 4px solid #DC2626;"><div class="term-label">Saídas Líquidas (-)</div><div class="term-amount" style="color:#DC2626;">R$ {t_desp:,.2f}</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br><hr style='border: 1px solid rgba(15,23,42,0.06);'><br>", unsafe_allow_html=True)
        
        df_desp = df_dash[df_dash["Tipo"] == "Despesa"]
        if not df_desp.empty and df_desp["Valor"].sum() > 0:
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                fig1 = px.pie(df_desp, values="Valor", names="Categoria", title="Distribuição por Categoria", hole=0.4, template="plotly")
                fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#475569"))
                st.plotly_chart(fig1, use_container_width=True)
            with c_g2:
                fig2 = px.pie(df_desp, values="Valor", names="Responsavel", title="Participação por Responsável", hole=0.4, template="plotly")
                fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#475569"))
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("O Dashboard está aguardando a importação ou registro de dados válidos.")

# ---------------------------------------------------------
# ABA LANÇAMENTOS
# ---------------------------------------------------------
with aba_lancamentos:
    st.subheader("Registrar Nova Movimentação Manual")
    col1, col2, col3 = st.columns(3)
    with col1:
        tipo = st.selectbox("Tipo de Movimento", ["Despesa", "Receita", "Investimento"])
        data_lancamento = st.date_input("Data do Ocorrido", datetime.today())
        valor_total = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
        parcelas = st.number_input("Número de Parcelas", min_value=1, max_value=120, value=1, step=1)
        status = st.radio("Status:", ["Pago", "Pendente"], horizontal=True)
    with col2:
        lista_cat = ["Alimentação", "Moradia", "Transporte", "Saúde", "Cuidados Pessoais", "Lazer", "Educação", "Assinaturas", "Impostos/Taxas", "Outros"] if tipo == "Despesa" else ["Renda Fixa", "Criptomoedas"] if tipo == "Investimento" else ["Salário", "Vendas/Comissão", "Outros"]
        cat_selecionada = st.selectbox("Categoria Principal", ["+ Adicionar Nova..."] + obter_opcoes("Categoria", lista_cat))
        categoria = st.text_input("Nova Categoria:") if cat_selecionada == "+ Adicionar Nova..." else cat_selecionada
        sub_selecionada = st.selectbox("Subcategoria", ["+ Adicionar Nova..."] + obter_opcoes("Subcategoria", ["Geral"]))
        subcategoria = st.text_input("Nova Subcategoria:") if sub_selecionada == "+ Adicionar Nova..." else sub_selecionada
    with col3:
        conta_selecionada = st.selectbox("Conta/Corretora", ["+ Adicionar Nova..."] + obter_opcoes("Conta_Cartao", ["Nubank", "Banco Inter", "Dinheiro/Pix", "BB", "Sicred", "Picpay"]))
        conta_cartao = st.text_input("Nova Conta:") if conta_selecionada == "+ Adicionar Nova..." else conta_selecionada
        resp_selecionado = st.selectbox("Responsável", ["+ Adicionar Novo..."] + obter_opcoes("Responsavel", ["Gabriel", "Tainá", "Casa/Conjunto", "Pais"]))
        responsavel = st.text_input("Novo Responsável:") if resp_selecionado == "+ Adicionar Novo..." else resp_selecionado
        descricao = st.text_input("Descrição Livre (Opcional)")

    if st.button("💾 Salvar Movimentação Manualmente", type="primary") and valor_total > 0:
        nova_linha = pd.DataFrame([{
            "ID": str(uuid.uuid4()), "Data": data_lancamento.strftime("%Y-%m-%d"), "Tipo": tipo,
            "Categoria": categoria, "Subcategoria": subcategoria, "Conta_Cartao": conta_cartao,
            "Valor": valor_total, "Descricao": descricao if descricao else "Sem descrição",
            "Parcela": "À vista", "Responsavel": responsavel, "Status": status
        }])
        df = pd.concat([df, nova_linha], ignore_index=True)
        df.to_csv(ARQUIVO_DADOS, index=False)
        st.success("Salvo com sucesso!")
        st.rerun()

# ---------------------------------------------------------
# ABA OPEN FINANCE INTERATIVA (PRO GRID DE INSTITUIÇÕES)
# ---------------------------------------------------------
with aba_openfinance:
    if st.session_state.of_step == "inicio":
        st.subheader("🔌 Hub de Integração Aberta (Open Finance)")
        st.write("Selecione sua instituição financeira para ativar o mapeamento automático de extratos.")
        
        # GRADE DE 8 BANCOS ESTILO BIG TECH (2 linhas de 4 colunas)
        row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
        with row1_col1:
            st.markdown('<div class="bank-card"><h4 style="color:#7C3AED;">💜 Nubank</h4><p style="color:#64748B; font-size:0.8rem;">API Oficial Ativa</p></div>', unsafe_allow_html=True)
            if st.button("Vincular Nubank"):
                st.session_state.of_banco, st.session_state.of_step = "Nubank", "auth_widget"
                st.rerun()
        with row1_col2:
            st.markdown('<div class="bank-card"><h4 style="color:#EA580C;">🧡 Banco Inter</h4><p style="color:#64748B; font-size:0.8rem;">API Oficial Ativa</p></div>', unsafe_allow_html=True)
            if st.button("Vincular Inter"):
                st.session_state.of_banco, st.session_state.of_step = "Banco Inter", "auth_widget"
                st.rerun()
        with row1_col3:
            st.markdown('<div class="bank-card"><h4 style="color:#1E3A8A;">💙 Itaú Unibanco</h4><p style="color:#64748B; font-size:0.8rem;">API Oficial Ativa</p></div>', unsafe_allow_html=True)
            if st.button("Vincular Itaú"):
                st.session_state.of_banco, st.session_state.of_step = "Itaú", "auth_widget"
                st.rerun()
        with row1_col4:
            st.markdown('<div class="bank-card"><h4 style="color:#DC2626;">❤️ Bradesco</h4><p style="color:#64748B; font-size:0.8rem;">API Oficial Ativa</p></div>', unsafe_allow_html=True)
            if st.button("Vincular Bradesco"):
                st.session_state.of_banco, st.session_state.of_step = "Bradesco", "auth_widget"
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        
        row2_col1, row2_col2, row2_col3, row2_col4 = st.columns(4)
        with row2_col1:
            st.markdown('<div class="bank-card"><h4 style="color:#E11D48;">🔴 Santander</h4><p style="color:#64748B; font-size:0.8rem;">API Oficial Ativa</p></div>', unsafe_allow_html=True)
            if st.button("Vincular Santander"):
                st.session_state.of_banco, st.session_state.of_step = "Santander", "auth_widget"
                st.rerun()
        with row2_col2:
            st.markdown('<div class="bank-card"><h4 style="color:#0284C7;">🔵 Caixa</h4><p style="color:#64748B; font-size:0.8rem;">API Oficial Ativa</p></div>', unsafe_allow_html=True)
            if st.button("Vincular Caixa"):
                st.session_state.of_banco, st.session_state.of_step = "Caixa", "auth_widget"
                st.rerun()
        with row2_col3:
            st.markdown('<div class="bank-card"><h4 style="color:#0F172A;">⚫ C6 Bank</h4><p style="color:#64748B; font-size:0.8rem;">API Oficial Ativa</p></div>', unsafe_allow_html=True)
            if st.button("Vincular C6 Bank"):
                st.session_state.of_banco, st.session_state.of_step = "C6 Bank", "auth_widget"
                st.rerun()
        with row2_col4:
            st.markdown('<div class="bank-card"><h4 style="color:#16A34A;">🟢 XP Investimentos</h4><p style="color:#64748B; font-size:0.8rem;">API Oficial Ativa</p></div>', unsafe_allow_html=True)
            if st.button("Vincular XP"):
                st.session_state.of_banco, st.session_state.of_step = "XP Investimentos", "auth_widget"
                st.rerun()

        st.markdown("<br><hr style='border: 1px solid rgba(15,23,42,0.06);'><br>", unsafe_allow_html=True)
        st.markdown("### 🔐 Entenda o Fluxo de Autorização Bancária (Padrão Pro de Segurança)")
        col_step1, col_step2, col_step3 = st.columns(3)
        with col_step1:
            st.markdown('<div class="step-box"><h4><span class="step-num">1</span> Redirecionamento</h4><p style="color: #475569; font-size: 0.9rem; margin-top:10px;">A plataforma abre uma janela segura criptografada conectada ao integrador oficial (Pluggy API). Você autoriza no ecossistema do seu próprio banco.</p></div>', unsafe_allow_html=True)
        with col_step2:
            st.markdown('<div class="step-box"><h4><span class="step-num">2</span> Consentimento</h4><p style="color: #475569; font-size: 0.9rem; margin-top:10px;">Você aprova o compartilhamento de dados em <b>modo apenas leitura (Read-Only)</b> através do aplicativo oficial do banco. Senhas não são compartilhadas.</p></div>', unsafe_allow_html=True)
        with col_step3:
            st.markdown('<div class="step-box"><h4><span class="step-num">3</span> Tokenização</h4><p style="color: #475569; font-size: 0.9rem; margin-top:10px;">O banco emite uma chave criptografada (Token). Nosso robô lê os extratos e consolida os gráficos automaticamente a cada transação.</p></div>', unsafe_allow_html=True)

    elif st.session_state.of_step == "auth_widget":
        st.markdown(f"""
            <div class="secure-widget">
                <h3 style="color:#4F46E5 !important; margin-bottom:5px;">🔒 Autorização de Leitura via Open Finance</h3>
                <p style="color:#64748B; font-size:0.9rem;">Instituição Alvo: <b>{st.session_state.of_banco} S.A.</b></p>
                <hr style="border-color: rgba(0,0,0,0.06); margin: 15px 0;">
                <p style="font-size:0.95rem; font-weight:600;">Esta aplicação solicita acesso temporário para fins de conciliação de fluxo de caixa:</p>
                <ul style="color:#475569; font-size:0.9rem; padding-left:20px; margin: 15px 0;">
                    <li>Histórico detalhado de depósitos, despesas, PIX e transferências (90 dias)</li>
                    <li>Saldos consolidados de contas correntes associadas</li>
                    <li>Faturas e lançamentos futuros de cartões de crédito</li>
                </ul>
                <p style="color:#94A3B8; font-size:0.85rem; margin-bottom:20px;">
                    🛡️ Criptografia AES-256 de ponta a ponta homologada pelo Banco Central. Modo Read-Only habilitado (impossível efetuar saques ou movimentações).
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        c_act1, c_act2 = st.columns([1, 4])
        with c_act1:
            if st.button("✔️ Autorizar Acesso", type="primary"):
                st.session_state.of_step = "mock_login_gateway"
                st.rerun()
        with c_act2:
            if st.button("❌ Cancelar Operação"):
                st.session_state.of_step = "inicio"
                st.rerun()

    elif st.session_state.of_step == "mock_login_gateway":
        # TELA INTERATIVA EXCLUSIVA DA VERSÃO 21: INTERFACE DE AUTENTICAÇÃO
        st.subheader(f"🔐 Portal de Autenticação Segura: {st.session_state.of_banco}")
        st.write("Insira as credenciais de leitura da sua conta bancária para estabelecer a ponte criptografada.")
        
        col_lg1, col_lg2 = st.columns(2)
        with col_lg1:
            st.text_input("Número da Agência (4 dígitos)", value="1234")
            st.text_input("Número da Conta com Dígito", value="56789-0")
        with col_lg2:
            st.info("💡 Ambiente de Demonstração Comercial: Você pode inserir qualquer número fictício nos campos ao lado para simular o processo real de integração com o cliente final.")
            
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔗 Confirmar Chave e Sincronizar", type="primary"):
            st.session_state.of_step = "processando"
            st.rerun()

    elif st.session_state.of_step == "processando":
        st.subheader("⚡ Sincronizando Contas Bancárias")
        barra = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Buscando chaves de acesso criptografadas (Tokens)...")
        time.sleep(0.8)
        barra.progress(30)
        
        status_text.text(f"Autenticando sessão no servidor seguro do {st.session_state.of_banco}...")
        time.sleep(1.0)
        barra.progress(70)
        
        status_text.text("Estruturando transações pendentes de Junho de 2026...")
        time.sleep(0.7)
        barra.progress(100)
        
        # CORE FIX: Nome da variável 'linhas_banco' corrigido e unificado para evitar NameError
        linhas_banco = pd.DataFrame([
            {
                "ID": str(uuid.uuid4()), "Data": "2026-06-02", "Tipo": "Despesa",
                "Categoria": "Transporte", "Subcategoria": "Importado", "Conta_Cartao": st.session_state.of_banco,
                "Valor": 28.90, "Descricao": f"UBER TRIP - {st.session_state.of_banco.upper()}", "Parcela": "À vista", 
                "Responsavel": "Gabriel", "Status": "Pago"
            },
            {
                "ID": str(uuid.uuid4()), "Data": "2026-06-02", "Tipo": "Receita",
                "Categoria": "Vendas/Comissão", "Subcategoria": "Importado", "Conta_Cartao": st.session_state.of_banco,
                "Valor": 350.00, "Descricao": f"PIX RECEBIDO - {st.session_state.of_banco.upper()}", "Parcela": "À vista", 
                "Responsavel": "Gabriel", "Status": "Pago"
            },
            {
                "ID": str(uuid.uuid4()), "Data": "2026-06-02", "Tipo": "Despesa",
                "Categoria": "Alimentação", "Subcategoria": "Importado", "Conta_Cartao": st.session_state.of_banco,
                "Valor": 45.50, "Descricao": f"IFOOD - {st.session_state.of_banco.upper()}", "Parcela": "À vista", 
                "Responsavel": "Tainá", "Status": "Pago"
            }
        ])
        
        df = pd.concat([df, linhas_banco], ignore_index=True)
        df.to_csv(ARQUIVO_DADOS, index=False)
        
        st.session_state.of_step = "inicio"
        st.success(f"🎉 ESPETÁCULO! Conexão estabelecida com o {st.session_state.of_banco}. Os dados foram injetados com sucesso!")
        st.balloons()
        time.sleep(1.5)
        st.rerun()

# ---------------------------------------------------------
# ABA GERENCIAR
# ---------------------------------------------------------
with aba_gerenciar:
    st.subheader("⚙️ Configurações de Sistema")
    if st.button("🗑 ZERAR BASE DE DADOS (Limpeza de Testes)", type="secondary"):
        if os.path.exists(ARQUIVO_DADOS):
            os.remove(ARQUIVO_DADOS)
            st.success("Base de dados limpa!")
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)
    with col_a: coluna_para_mudar = st.selectbox("Renomear em lote:", ["Responsavel", "Categoria", "Subcategoria", "Conta_Cartao", "Status"])
    valores_atuais = ["Nenhum dado"]
    if not df.empty and coluna_para_mudar in df.columns:
        lst = [x.strip() for x in df[coluna_para_mudar].dropna().astype(str).unique() if x.strip() not in ["", "nan"]]
        if lst: valores_atuais = sorted(lst)
    with col_b: valor_antigo = st.selectbox("Nome atual:", valores_atuais)
    with col_c: valor_novo = st.text_input("Novo nome:")
    if st.button("Aplicar Mudança", type="secondary") and valor_antigo != "Nenhum dado" and valor_novo.strip() != "":
        df.loc[df[coluna_para_mudar].astype(str).str.strip() == valor_antigo, coluna_para_mudar] = valor_novo
        df.to_csv(ARQUIVO_DADOS, index=False)
        st.success("Alterado!")
        st.rerun()
        
    st.markdown("---")
    if not df.empty:
        df_editado = st.data_editor(df, use_container_width=True, num_rows="dynamic", column_config={"ID": None} if "ID" in df.columns else {})
        if st.button("💾 Salvar Edições Manuais", type="primary"):
            df_editado.to_csv(ARQUIVO_DADOS, index=False)
            st.rerun()

# ---------------------------------------------------------
# ABA IMPORTADOR
# ---------------------------------------------------------
with aba_importar:
    st.subheader("📥 Importação Direta de Matrizes Excel")
    arquivo_upado = st.file_uploader("Arquivo Excel (.xlsx, .xls)", type=['xlsx', 'xls'])
    
    if arquivo_upado:
        try:
            excel_file = pd.ExcelFile(arquivo_upado, engine='openpyxl')
            abas_disponiveis = excel_file.sheet_names
            aba_selecionada = st.selectbox("Selecione o Mês (Aba) que deseja importar:", abas_disponiveis)
            
            if st.button("🚀 Processar Aba Selecionada", type="primary"):
                df_bruto = excel_file.parse(aba_selecionada, header=None)
                novos_dados = []
                
                meses_map = {
                    "JANEIRO": "01", "FEVEREIRO": "02", "MARÇO": "03", "MARCO": "03",
                    "ABRIL": "04", "MAIO": "05", "JUNHO": "06", "JULHO": "07", 
                    "AGOSTO": "08", "SETEMBRO": "09", "OUTUBRO": "10", "NOVEMBRO": "11", "DEZEMBRO": "12"
                }
                mes_num_alvo = meses_map.get(aba_selecionada.upper().strip(), "06")
                
                header_idx = -1
                for i in range(min(15, len(df_bruto))):
                    linha_str = " ".join([str(x).upper() for x in df_bruto.iloc[i].fillna("")]).upper()
                    if "DATA" in linha_str and ("RECEITA" in linha_str or "DESPESA" in linha_str):
                        header_idx = i
                        break
                
                if header_idx != -1:
                    nomes_colunas = []
                    for col_idx in range(len(df_bruto.columns)):
                        val_row2 = str(df_bruto.iloc[header_idx, col_idx]).strip().upper()
                        val_row1 = str(df_bruto.iloc[header_idx - 1, col_idx]).strip().upper() if header_idx > 0 else ""
                        
                        if val_row2 not in ["", "NAN", "NONE", "VAZIO", "-"]: nome_final = val_row2
                        elif val_row1 not in ["", "NAN", "NONE", "VAZIO", "-"]: nome_final = val_row1
                        else: nome_final = f"COL_{col_idx}"
                        nomes_colunas.append(nome_final)
                    
                    df_dados = df_bruto.iloc[header_idx+1:].copy()
                    df_dados.columns = nomes_colunas
                    
                    col_data = next((c for c in nomes_colunas if "DATA" in c), None)
                    col_rec = next((c for c in nomes_colunas if "RECEITA" in c), None)
                    col_desp = next((c for c in nomes_colunas if "DESPESA" in c), None)
                    col_desc = next((c for c in nomes_colunas if "DESCRI" in c), None)
                    col_cat = next((c for c in nomes_colunas if "CATEGORIA" in c), None)
                    col_banco = next((c for c in nomes_colunas if "BANC" in c or "CONT" in c), None)
                    col_ano = next((c for c in nomes_colunas if "ANO" in c), None)
                    
                    mapping_responsaveis = {"GABRIEL": "Gabriel", "THATA": "Tainá", "NÓS": "Casa/Conjunto", "PAI/MÃE": "Pais"}
                    
                    def limpa_valor(v):
                        if pd.isna(v): return 0.0
                        vs = str(v).upper().replace('R$', '').strip()
                        if vs in ['', '-', '0', '0.0', '0,0']: return 0.0
                        if ',' in vs and '.' in vs:
                            if vs.rfind(',') > vs.rfind('.'): vs = vs.replace('.', '').replace(',', '.')
                            else: vs = vs.replace(',', '')
                        elif ',' in vs: vs = vs.replace(',', '.')
                        try: return abs(float(vs))
                        except: return 0.0

                    for _, row in df_dados.iterrows():
                        if col_data and str(row[col_data]).strip().upper() == "TOTAL": continue
                        data_orig = str(row[col_data]).strip() if col_data else ""
                        if data_orig in ["", "nan", "NaT", "None", "VAZIO"]: continue
                        
                        # CORE FIX: Nome das funções 'limpa_valor' unificado em toda a estrutura
                        v_rec = limpa_valor(row[col_rec]) if col_rec else 0.0
                        v_desp = limpa_valor(row[col_desp]) if col_desp else 0.0
                        tipo_linha = "Receita" if v_rec > 0 else "Despesa"
                        
                        splits_encontrados = {}
                        for keyword, label in mapping_responsaveis.items():
                            col_alvo = next((c for c in nomes_colunas if keyword in c), None)
                            if col_alvo and pd.notna(row[col_alvo]):
                                val_sub = limpa_valor(row[col_alvo])
                                if val_sub > 0: splits_encontrados[label] = val_sub
                        
                        def registrar(val_item, resp_item):
                            novos_dados.append({
                                "ID": str(uuid.uuid4()), "Data": f"2026-{mes_num_alvo}-01", "Tipo": tipo_linha,
                                "Categoria": str(row[col_cat]).title() if col_cat and pd.notna(row[col_cat]) else "Importado",
                                "Subcategoria": "Importado",
                                "Conta_Cartao": str(row[col_banco]).strip() if col_banco and pd.notna(row[col_banco]) and str(row[col_banco]).strip() != "-" else "Dinheiro/Pix",
                                "Valor": val_item, "Descricao": str(row[col_desc]).strip() if col_desc and pd.notna(row[col_desc]) else "Sem descrição",
                                "Parcela": "À vista", "Responsavel": resp_item, "Status": "Pago"
                            })

                        if splits_encontrados:
                            for resp_nome, val_repartido in splits_encontrados.items(): registrar(val_repartido, resp_nome)
                        else:
                            valor_total_linha = v_rec if v_rec > 0 else v_desp
                            if valor_total_linha > 0: registrar(valor_total_linha, "Gabriel")
                        
                if novos_dados:
                    df_novos = pd.DataFrame(novos_dados)
                    df = pd.concat([df, df_novos], ignore_index=True)
                    df.to_csv(ARQUIVO_DADOS, index=False)
                    st.success(f"🎉 Processamento Concluído com Sucesso!")
                    st.balloons()
                    st.rerun()
        except Exception as e:
            st.error(f"Erro crítico: {e}")