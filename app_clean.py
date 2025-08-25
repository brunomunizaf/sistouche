#!/usr/bin/env python3
"""
Sistema de Orçamentos de Projetos com CPQ Integrado
Streamlit app para gerenciamento de clientes e orçamentos
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from supabase_manager import SupabaseManager

# Configuração da página
st.set_page_config(
    page_title="Sistema de Orçamentos - Touché",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        color: #1f77b4;
        text-align: center;
        font-size: 2.5rem;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border: none;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    .stButton > button:hover {
        background-color: #0d5aa7;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar conexão com banco de dados
@st.cache_resource
def init_db():
    return SupabaseManager()

db = init_db()

# Sistema de autenticação
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login - Sistema de Orçamentos")
    
    with st.form("login"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            if username and password:
                result = db.autenticar_usuario(username, password)
                if result['success']:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = result['user']['role']
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"❌ {result['error']}")
            else:
                st.error("❌ Preencha todos os campos!")
    
    st.info("👥 **Usuários disponíveis:**")
    st.write("- **bruno** (admin): 28187419")
    st.write("- **melissa** (admin): 130188491") 
    st.write("- **julia** (atendimento): 5912849123")
    
    st.stop()

# Sidebar
st.sidebar.title("📋 Menu")

# Informações do usuário logado
if 'username' in st.session_state:
    user_role = st.session_state.get('user_role', 'user')
    if user_role == 'admin':
        role_display = "👑 Administrador"
    elif user_role == 'atendimento':
        role_display = "👩 Atendimento"
    else:
        role_display = "👤 Usuário"
    st.sidebar.success(f"{role_display}: {st.session_state.username}")

# Definir páginas disponíveis baseado no perfil
if 'user_role' in st.session_state:
    if st.session_state.user_role == 'admin':
        # Administrador tem acesso a tudo
        paginas_disponiveis = [
            "🏠 Dashboard", 
            "👥 Clientes", 
            "🧮 CPQ - Orçamento", 
            "📊 Orçamentos", 
            "📈 Relatórios"
        ]
    elif st.session_state.user_role == 'atendimento':
        # Atendimento tem acesso ao CPQ e visualização
        paginas_disponiveis = [
            "🏠 Dashboard", 
            "👥 Clientes", 
            "🧮 CPQ - Orçamento", 
            "📊 Orçamentos"
        ]
    else:
        # Usuário comum tem acesso limitado
        paginas_disponiveis = [
            "🏠 Dashboard", 
            "👥 Clientes"
        ]
else:
    # Fallback para usuários sem perfil definido
    paginas_disponiveis = ["🏠 Dashboard", "👥 Clientes"]

pagina = st.sidebar.selectbox(
    "Selecione a página:",
    paginas_disponiveis
)

# Botão de logout
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    if 'username' in st.session_state:
        del st.session_state.username
    st.success("✅ Logout realizado com sucesso!")
    st.rerun()

# Função para exibir dashboard
def dashboard():
    st.markdown('<h1 class="main-header">Sistema de Orçamentos de Projetos</h1>', unsafe_allow_html=True)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        clientes_df = db.buscar_clientes()
        st.metric("Total de Clientes", len(clientes_df))
    
    with col2:
        orcamentos_df = db.buscar_orcamentos()
        st.metric("Total de Projetos", len(orcamentos_df))
    
    with col3:
        st.metric("Total de Orçamentos", len(orcamentos_df))
    
    with col4:
        if not orcamentos_df.empty:
            total_vendas = orcamentos_df['total'].sum()
            st.metric("Total em Vendas", f"R$ {total_vendas:,.2f}")
        else:
            st.metric("Total em Vendas", "R$ 0,00")
    
    # Gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        if not orcamentos_df.empty:
            # Gráfico de orçamentos por mês
            orcamentos_df['data_orcamento'] = pd.to_datetime(orcamentos_df['data_orcamento'])
            orcamentos_df['mes'] = orcamentos_df['data_orcamento'].dt.strftime('%Y-%m')
            orcamentos_por_mes = orcamentos_df.groupby('mes').size().reset_index(name='quantidade')
            
            fig = px.line(orcamentos_por_mes, x='mes', y='quantidade', 
                         title='Orçamentos por Mês', markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if not orcamentos_df.empty:
            # Gráfico de status dos orçamentos
            status_counts = orcamentos_df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title='Status dos Orçamentos')
            st.plotly_chart(fig, use_container_width=True)
    
    # Últimos orçamentos
    st.subheader("📋 Últimos Orçamentos")
    if not orcamentos_df.empty:
        ultimos_orcamentos = orcamentos_df.head(5)[['numero_orcamento', 'cliente_nome', 'total', 'status', 'data_orcamento']]
        st.dataframe(ultimos_orcamentos, use_container_width=True)
    else:
        st.info("Nenhum orçamento encontrado.")

# Função para gerenciar clientes
def formatar_cpf_cnpj(cpf_cnpj, tipo_pessoa):
    """Formata CPF/CNPJ baseado no tipo de pessoa"""
    if not cpf_cnpj or pd.isna(cpf_cnpj) or cpf_cnpj == '':
        return '-'
    
    # Remove caracteres não numéricos
    numeros = ''.join(filter(str.isdigit, str(cpf_cnpj)))
    
    if tipo_pessoa == 'fisica':
        # Formata CPF: XXX.XXX.XXX-XX
        if len(numeros) == 11:
            return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}"
        else:
            return cpf_cnpj
    elif tipo_pessoa == 'juridica':
        # Formata CNPJ: XX.XXX.XXX/XXXX-XX
        if len(numeros) == 14:
            return f"{numeros[:2]}.{numeros[2:5]}.{numeros[5:8]}/{numeros[8:12]}-{numeros[12:]}"
        else:
            return cpf_cnpj
    else:
        return cpf_cnpj

def clientes():
    st.title("👥 Touché - Cadastro de Clientes")
    st.markdown("Aplicação Streamlit para cadastro e gerenciamento de clientes da Touché.")
    
    # Definir abas baseado no perfil do usuário
    if 'user_role' in st.session_state and (st.session_state.user_role == 'admin' or st.session_state.user_role == 'atendimento'):
        # Administrador e Atendimento têm acesso a todas as abas de clientes
        tab1, tab2, tab3 = st.tabs(["📝 Cadastrar Cliente", "📋 Lista de Clientes", "🔍 Buscar Cliente"])
    else:
        # Usuário comum só pode visualizar e buscar
        tab1, tab2 = st.tabs(["📋 Lista de Clientes", "🔍 Buscar Cliente"])
    
    # Aba de cadastro (para admin e atendimento)
    if 'user_role' in st.session_state and (st.session_state.user_role == 'admin' or st.session_state.user_role == 'atendimento'):
        with tab1:
            st.subheader("Novo Cliente")
            
            with st.form("novo_cliente"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nome = st.text_input("Nome/Razão Social *", placeholder="Ex: João Silva ou Empresa ABC Ltda")
                    email = st.text_input("Email", placeholder="exemplo@email.com")
                    telefone = st.text_input("Telefone", placeholder="(11) 99999-9999")
                
                with col2:
                    tipo_pessoa = st.selectbox("Tipo de Pessoa *", ["fisica", "juridica"])
                    cpf_cnpj = st.text_input("CPF/CNPJ *", placeholder="000.000.000-00 ou 00.000.000/0000-00")
                    endereco = st.text_area("Endereço/Representante", placeholder="Endereço completo ou Representante: Nome")
                
                submitted = st.form_submit_button("Cadastrar Cliente")
                
                if submitted:
                    if nome and cpf_cnpj:
                        try:
                            cliente_id = db.inserir_cliente(nome, email, telefone, cpf_cnpj, endereco, tipo_pessoa)
                            if cliente_id:
                                st.success(f"✅ Cliente cadastrado com sucesso! ID: {cliente_id}")
                                st.rerun()
                            else:
                                st.error("❌ Erro ao cadastrar cliente")
                        except Exception as e:
                            st.error(f"❌ Erro ao cadastrar cliente: {str(e)}")
                    else:
                        st.error("❌ Preencha os campos obrigatórios!")
    
    # Aba de listagem
    with tab2:
        st.subheader("Lista de Clientes")
        
        clientes_df = db.buscar_clientes()
        
        if not clientes_df.empty:
            # Formatar CPF/CNPJ para exibição
            clientes_df['cpf_cnpj_formatado'] = clientes_df.apply(
                lambda row: formatar_cpf_cnpj(row['cpf_cnpj'], row['pessoa']), axis=1
            )
            
            # Selecionar apenas as colunas necessárias
            colunas_exibicao = ['id', 'nome', 'email', 'telefone', 'cpf_cnpj_formatado', 'representante']
            resultados_exibicao = clientes_df[colunas_exibicao].copy()
            
            # Renomear colunas
            resultados_exibicao = resultados_exibicao.rename(columns={
                'id': 'ID',
                'nome': 'Nome/Razão Social',
                'email': 'Email',
                'telefone': 'Contato',
                'cpf_cnpj_formatado': 'CPF/CNPJ',
                'representante': 'Representante'
            })
            
            st.dataframe(resultados_exibicao, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum cliente cadastrado ainda.")
    
    # Aba de busca
    with tab3:
        st.subheader("Buscar Cliente")
        
        clientes_df = db.buscar_clientes()
        
        if not clientes_df.empty:
            # Campo de busca
            termo_busca = st.text_input("Digite o nome, email ou CPF/CNPJ para buscar")
            
            if termo_busca:
                # Buscar por nome, email ou CPF/CNPJ
                resultados = clientes_df[
                    clientes_df['nome'].str.contains(termo_busca, case=False, na=False) |
                    clientes_df['email'].str.contains(termo_busca, case=False, na=False) |
                    clientes_df['cpf_cnpj'].str.contains(termo_busca, case=False, na=False)
                ]
                
                if not resultados.empty:
                    # Formatar CPF/CNPJ para exibição
                    resultados['cpf_cnpj_formatado'] = resultados.apply(
                        lambda row: formatar_cpf_cnpj(row['cpf_cnpj'], row['pessoa']), axis=1
                    )
                    
                    # Selecionar apenas as colunas necessárias
                    colunas_exibicao = ['id', 'nome', 'email', 'telefone', 'cpf_cnpj_formatado', 'representante']
                    resultados_exibicao = resultados[colunas_exibicao].copy()
                    
                    # Renomear colunas
                    resultados_exibicao = resultados_exibicao.rename(columns={
                        'id': 'ID',
                        'nome': 'Nome/Razão Social',
                        'email': 'Email',
                        'telefone': 'Contato',
                        'cpf_cnpj_formatado': 'CPF/CNPJ',
                        'representante': 'Representante'
                    })
                    
                    st.dataframe(resultados_exibicao, use_container_width=True, hide_index=True)
                else:
                    st.warning("Nenhum cliente encontrado com os critérios informados.")
            else:
                st.info("Digite um termo para buscar clientes.")
        else:
            st.info("Nenhum cliente cadastrado ainda.")

# Função para criar novo orçamento usando CPQ
def novo_orcamento():
    # Verificar permissão
    if 'user_role' in st.session_state and st.session_state.user_role not in ['admin', 'atendimento']:
        st.warning("⚠️ Acesso restrito. Apenas administradores e atendimento podem criar orçamentos.")
        st.info("Entre em contato com o administrador para solicitar acesso.")
        return
    
    st.title("🧮 CPQ - Orçamento de Caixas Customizadas")
    st.markdown("Sistema de cálculo automático de custos para caixas personalizadas")
    
    # Buscar dados necessários
    clientes_df = db.buscar_clientes()
    
    if clientes_df.empty:
        st.error("É necessário cadastrar pelo menos um cliente antes de criar orçamentos.")
        return
    
    st.subheader("📋 Informações do Cliente")
    
    # Seleção do cliente
    cliente_options = {f"{row['nome']} (ID: {row['id']})": row['id'] for _, row in clientes_df.iterrows()}
    cliente_selecionado = st.selectbox("Cliente *", options=list(cliente_options.keys()))
    cliente_id = cliente_options[cliente_selecionado]
    
    # Data de validade
    data_validade = st.date_input("Data de validade", value=datetime.now() + timedelta(days=30))
    
    # Observações
    observacoes = st.text_area("Observações")
    
    st.subheader("📦 Especificações da Caixa")
    
    # Dimensões
    col1, col2, col3 = st.columns(3)
    with col1:
        largura_cm = st.number_input("Largura (cm) *", min_value=0.1, value=20.0, step=0.1)
    with col2:
        altura_cm = st.number_input("Altura (cm) *", min_value=0.1, value=15.0, step=0.1)
    with col3:
        profundidade_cm = st.number_input("Profundidade (cm) *", min_value=0.1, value=10.0, step=0.1)
    
    # Tipo de tampa e material
    col1, col2 = st.columns(2)
    with col1:
        modelo = st.selectbox(
            "Tipo de Tampa *",
            ["Tampa Solta", "Tampa Livro", "Tampa Luva", "Tampa Imã", "Tampa Redonda"]
        )
    with col2:
        material = st.selectbox(
            "Material *",
            ["Papelão", "Acrílico"]
        )
    
    # Quantidade
    quantidade = st.number_input("Quantidade de caixas *", min_value=1, value=1, step=1)
    
    st.subheader("🔧 Opções Adicionais")
    
    # Opções de berço e nicho
    col1, col2 = st.columns(2)
    with col1:
        berco = st.checkbox("Incluir berço")
    with col2:
        nicho = st.checkbox("Incluir nicho", disabled=not berco)
    
    # Opções de impressão
    col1, col2 = st.columns(2)
    with col1:
        serigrafia = st.checkbox("Usar serigrafia")
        if serigrafia:
            num_cores_serigrafia = st.number_input("Número de cores", min_value=1, value=1, step=1)
            num_impressoes_serigrafia = st.number_input("Número de impressões", min_value=1, value=1, step=1)
        else:
            num_cores_serigrafia = 1
            num_impressoes_serigrafia = 1
    with col2:
        usar_impressao_digital = st.checkbox("Usar impressão digital")
        if usar_impressao_digital:
            tipo_impressao = st.selectbox("Tipo de impressão", ["A4", "A3"])
        else:
            tipo_impressao = "A4"
    
    # Revestimento (apenas para papelão)
    if material == "Papelão":
        tipo_revestimento = st.selectbox(
            "Tipo de revestimento",
            ["Nenhum", "Papel", "Vinil UV"]
        )
    else:
        tipo_revestimento = "Nenhum"
    
    # Outras opções
    col1, col2 = st.columns(2)
    with col1:
        usar_cola_quente = st.checkbox("Usar cola quente")
        usar_cola_isopor = st.checkbox("Usar cola isopor")
    with col2:
        metros_fita = st.number_input("Metros de fita", min_value=0.0, value=0.0, step=0.1)
        num_rebites = st.number_input("Número de rebites", min_value=0, value=0, step=1)
    
    # Markup
    markup = st.number_input("Markup (%)", min_value=0.0, value=0.0, step=0.1, help="Percentual de lucro sobre o custo")
    markup_decimal = markup / 100
    
    # Botão de cálculo
    if st.button("🧮 Calcular Orçamento"):
        
        # Validar campos obrigatórios
        if not largura_cm or not altura_cm or not profundidade_cm or not quantidade:
            st.error("Preencha todos os campos obrigatórios!")
            return
        
        try:
            # Preparar dados para o CPQ
            dados_calculo = {
                "largura_cm": largura_cm,
                "altura_cm": altura_cm,
                "profundidade_cm": profundidade_cm,
                "modelo": modelo,
                "material": material,
                "quantidade": quantidade,
                "berco": berco,
                "nich": nicho,
                "serigrafia": serigrafia,
                "num_cores_serigrafia": num_cores_serigrafia,
                "num_impressoes_serigrafia": num_impressoes_serigrafia,
                "usar_impressao_digital": usar_impressao_digital,
                "tipo_impressao": tipo_impressao,
                "tipo_revestimento": tipo_revestimento,
                "usar_cola_quente": usar_cola_quente,
                "usar_cola_isopor": usar_cola_isopor,
                "metros_fita": metros_fita,
                "num_rebites": num_rebites,
                "markup": markup_decimal
            }
            
            # Calcular usando o CPQ
            with st.spinner("Calculando custos com CPQ..."):
                from cpq_calculator import calcular_custo_caixa_completo
                
                # Converter cm para mm para o CPQ
                largura_mm = largura_cm * 10
                altura_mm = altura_cm * 10
                profundidade_mm = profundidade_cm * 10
                
                resultado = calcular_custo_caixa_completo(
                    largura_mm=largura_mm,
                    altura_mm=altura_mm,
                    profundidade_mm=profundidade_mm,
                    modelo=modelo,
                    material=material,
                    quantidade=quantidade,
                    berco=berco,
                    nicho=nicho,
                    serigrafia=serigrafia,
                    num_cores_serigrafia=num_cores_serigrafia,
                    num_impressoes_serigrafia=num_impressoes_serigrafia,
                    usar_impressao_digital=usar_impressao_digital,
                    tipo_impressao=tipo_impressao,
                    tipo_revestimento=tipo_revestimento,
                    usar_cola_quente=usar_cola_quente,
                    usar_cola_isopor=usar_cola_isopor,
                    metros_fita=metros_fita,
                    num_rebites=num_rebites,
                    markup=markup_decimal
                )
            
            if resultado:
                st.success("✅ Cálculo CPQ concluído com sucesso!")
                
                # Mostrar resultados
                st.subheader("💰 Resultado do Cálculo")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Preço Unitário", f"R$ {resultado.get('preco_unitario', 0):.2f}")
                    st.metric("Preço Total", f"R$ {resultado.get('preco_total', 0):.2f}")
                    st.metric("Custo Fixo Unitário", f"R$ {resultado.get('custo_fixo_unitario', 0):.2f}")
                
                with col2:
                    st.metric("Custo Papelão", f"R$ {resultado.get('custo_papelao', 0):.2f}")
                    st.metric("Custo Revestimento", f"R$ {resultado.get('custo_revestimento', 0):.2f}")
                    st.metric("Custo Cola PVA", f"R$ {resultado.get('custo_cola_pva', 0):.2f}")
                
                # Detalhes técnicos
                st.subheader("📊 Detalhes Técnicos")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Área Papelão:** {resultado.get('area_papelao_m2', 0):.4f} m²")
                    st.write(f"**Área Revestimento:** {resultado.get('area_revestimento_m2', 0):.4f} m²")
                    st.write(f"**Cola PVA:** {resultado.get('ml_cola_pva', 0):.2f} ml")
                    st.write(f"**Cola Adesiva:** {resultado.get('ml_cola_pva', 0):.2f} ml")
                
                with col2:
                    st.write(f"**Caixas por Mês:** {resultado.get('caixas_por_mes', 0)}")
                    st.write(f"**Custo Serigrafia:** R$ {resultado.get('custo_serigrafia', 0):.2f}")
                    st.write(f"**Custo Impressão:** R$ {resultado.get('custo_impressao', 0):.2f}")
                    st.write(f"**Custo Fita:** R$ {resultado.get('custo_fita', 0):.2f}")
                
                # Botão para salvar orçamento
                if st.button("💾 Salvar Orçamento no Sistema"):
                    try:
                        # Criar item para o sistema de orçamentos
                        item_orcamento = {
                            'descricao': f"Caixa {modelo} - {material} ({largura_cm}x{altura_cm}x{profundidade_cm}cm)",
                            'quantidade': quantidade,
                            'preco_unitario': resultado.get('preco_unitario', 0)
                        }
                        
                        orcamento_id, numero_orcamento = db.inserir_orcamento(
                            cliente_id, data_validade, observacoes, [item_orcamento]
                        )
                        
                        st.success(f"✅ Orçamento salvo com sucesso! Número: {numero_orcamento}")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar orçamento: {str(e)}")
                
                # Botão para gerar PDF
                if st.button("📄 Gerar PDF do Orçamento"):
                    try:
                        from pdf_generator import gerar_pdf_calculo
                        
                        # Gerar PDF
                        pdf_bytes = gerar_pdf_calculo(
                            dados_calculo=dados_calculo,
                            resultado=resultado,
                            cliente_info={
                                'nome': cliente_selecionado,
                                'data_validade': data_validade,
                                'observacoes': observacoes
                            }
                        )
                        
                        # Download do PDF
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"orcamento_cpq_{numero_orcamento if 'numero_orcamento' in locals() else 'temp'}.pdf",
                            mime="application/pdf"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar PDF: {str(e)}")
            
            else:
                st.error("❌ Erro no cálculo CPQ")
                
        except Exception as e:
            st.error(f"❌ Erro ao calcular orçamento: {str(e)}")
            st.info("Verifique se todos os módulos CPQ estão funcionando corretamente.")

# Função para visualizar orçamentos
def orcamentos():
    # Verificar permissão
    if 'user_role' in st.session_state and st.session_state.user_role not in ['admin', 'atendimento']:
        st.warning("⚠️ Acesso restrito. Apenas administradores e atendimento podem visualizar orçamentos.")
        st.info("Entre em contato com o administrador para solicitar acesso.")
        return
    
    st.title("📊 Orçamentos")
    
    orcamentos_df = db.buscar_orcamentos()
    
    if not orcamentos_df.empty:
        # Formatação das datas
        orcamentos_df['data_orcamento'] = pd.to_datetime(orcamentos_df['data_orcamento']).dt.strftime('%d/%m/%Y %H:%M')
        orcamentos_df['data_validade'] = pd.to_datetime(orcamentos_df['data_validade']).dt.strftime('%d/%m/%Y')
        orcamentos_df['total'] = orcamentos_df['total'].apply(lambda x: f"R$ {x:.2f}")
        
        # Filtros
        col1, col2 = st.columns(2)
        
        with col1:
            status_filter = st.selectbox("Filtrar por status", ["Todos"] + list(orcamentos_df['status'].unique()))
        
        with col2:
            search = st.text_input("Buscar por número ou cliente")
        
        # Aplicar filtros
        filtered_df = orcamentos_df.copy()
        
        if status_filter != "Todos":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        
        if search:
            filtered_df = filtered_df[
                filtered_df['numero_orcamento'].str.contains(search, case=False) |
                filtered_df['cliente_nome'].str.contains(search, case=False)
            ]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Download dos dados
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="orcamentos.csv",
            mime="text/csv"
        )
        
        # Visualizar orçamento específico
        st.subheader("🔍 Visualizar Orçamento")
        orcamento_id = st.number_input("Digite o ID do orçamento para visualizar", min_value=1, value=1)
        
        if st.button("Visualizar"):
            orcamento, itens = db.buscar_orcamento_por_id(orcamento_id)
            
            if orcamento is not None:
                st.subheader(f"Orçamento #{orcamento['numero_orcamento']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Cliente:** {orcamento['cliente_nome']}")
                    st.write(f"**Email:** {orcamento['cliente_email']}")
                    st.write(f"**Telefone:** {orcamento['cliente_telefone']}")
                
                with col2:
                    st.write(f"**Data do orçamento:** {pd.to_datetime(orcamento['data_orcamento']).strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"**Data de validade:** {pd.to_datetime(orcamento['data_validade']).strftime('%d/%m/%Y')}")
                    st.write(f"**Status:** {orcamento['status']}")
                
                if orcamento['observacoes']:
                    st.write(f"**Observações:** {orcamento['observacoes']}")
                
                st.subheader("Itens/Serviços do Projeto")
                if not itens.empty:
                    itens_display = itens[['produto_nome', 'quantidade', 'preco_unitario', 'subtotal']].copy()
                    itens_display['preco_unitario'] = itens_display['preco_unitario'].apply(lambda x: f"R$ {x:.2f}")
                    itens_display['subtotal'] = itens_display['subtotal'].apply(lambda x: f"R$ {x:.2f}")
                    st.dataframe(itens_display, use_container_width=True)
                    
                    st.subheader(f"💰 Total: R$ {orcamento['total']:.2f}")
                else:
                    st.info("Nenhum item encontrado para este projeto.")
            else:
                st.error("Orçamento não encontrado!")
    else:
        st.info("Nenhum orçamento encontrado.")

# Função para relatórios
def relatorios():
    # Verificar permissão
    if 'user_role' in st.session_state and st.session_state.user_role not in ['admin', 'atendimento']:
        st.warning("⚠️ Acesso restrito. Apenas administradores e atendimento podem acessar relatórios.")
        st.info("Entre em contato com o administrador para solicitar acesso.")
        return
    
    st.title("📈 Relatórios")
    st.info("📊 Funcionalidade de relatórios em desenvolvimento...")

# Navegação principal
if pagina == "🏠 Dashboard":
    dashboard()
elif pagina == "👥 Clientes":
    clientes()
elif pagina == "🧮 CPQ - Orçamento":
    novo_orcamento()
elif pagina == "📊 Orçamentos":
    orcamentos()
elif pagina == "📈 Relatórios":
    relatorios()

