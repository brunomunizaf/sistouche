import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from supabase_manager import SupabaseManager
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(
    page_title="Sistema de Orçamentos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicialização do Supabase
@st.cache_resource
def get_database():
    return SupabaseManager()

db = get_database()

# Função de autenticação
def check_authentication():
    """Verifica se o usuário está autenticado"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        st.title("🔐 Login - Sistema Touché")
        st.markdown("---")
        
        # Formulário de login
        with st.form("login_form"):
            st.subheader("Acesse o Sistema")
            
            username = st.text_input("Usuário", placeholder="Digite seu usuário")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("🔑 Entrar")
            with col2:
                if st.form_submit_button("❌ Cancelar"):
                    st.stop()
            
            if submitted:
                # Usar o Supabase Manager para autenticação
                auth_result = db.autenticar_usuario(username, password)
                
                if auth_result['success']:
                    st.session_state.authenticated = True
                    st.session_state.username = auth_result['user']['email']
                    st.session_state.user_role = auth_result['user']['role']
                    st.success("✅ Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error(f"❌ {auth_result['error']}")        
        st.stop()
    
    return True

# Verificar autenticação
check_authentication()

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #c3e6cb;
    }
</style>
""", unsafe_allow_html=True)

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
                    contato = st.text_input("Contato *", placeholder="Ex: (11) 99999-9999")
                    representante = st.text_input("Representante (opcional)", placeholder="Ex: Maria Silva")
                
                with col2:
                    email = st.text_input("Email *", placeholder="Ex: joao@email.com")
                    inscricao = st.text_input("CPF/CNPJ (opcional)", placeholder="Ex: 123.456.789-01 ou 12.345.678/0001-90")
                    pessoa = st.selectbox("Tipo de Pessoa *", ["fisica", "juridica"], format_func=lambda x: "Pessoa Física" if x == "fisica" else "Pessoa Jurídica")
                
                submitted = st.form_submit_button("Cadastrar Cliente")
                
                if submitted:
                    # Validações
                    erros = []
                    
                    # Validação do nome
                    if not nome or nome.strip() == "":
                        erros.append("Nome/Razão Social é obrigatório")
                    elif len(nome.strip()) < 3:
                        erros.append("Nome/Razão Social deve ter pelo menos 3 caracteres")
                    
                    # Validação do contato
                    if not contato or contato.strip() == "":
                        erros.append("Contato é obrigatório")
                    elif len(contato.strip()) < 8:
                        erros.append("Contato deve ter pelo menos 8 caracteres")
                    
                    # Validação do email
                    if not email or email.strip() == "":
                        erros.append("Email é obrigatório")
                    else:
                        email_limpo = email.strip()
                        if not '@' in email_limpo or not '.' in email_limpo:
                            erros.append("Email deve ter formato válido")
                        elif len(email_limpo) < 5:
                            erros.append("Email deve ter pelo menos 5 caracteres")
                        elif email_limpo.count('@') != 1:
                            erros.append("Email deve conter exatamente um @")
                        elif email_limpo.startswith('@') or email_limpo.endswith('@'):
                            erros.append("Email não pode começar ou terminar com @")
                        elif email_limpo.startswith('.') or email_limpo.endswith('.'):
                            erros.append("Email não pode começar ou terminar com ponto")
                    
                    # Validação de CPF/CNPJ baseada no tipo de pessoa
                    if inscricao and inscricao.strip() != "":
                        inscricao_limpa = inscricao.replace('.', '').replace('-', '').replace('/', '').strip()
                        
                        # Verificar se contém apenas números
                        if not inscricao_limpa.isdigit():
                            erros.append("CPF/CNPJ deve conter apenas números")
                        else:
                            if pessoa == "fisica":
                                if len(inscricao_limpa) != 11:
                                    erros.append("CPF deve ter 11 dígitos para pessoa física")
                                else:
                                    # Validação básica de CPF (soma dos dígitos)
                                    if inscricao_limpa == inscricao_limpa[0] * 11:
                                        erros.append("CPF não pode ter todos os dígitos iguais")
                            elif pessoa == "juridica":
                                if len(inscricao_limpa) != 14:
                                    erros.append("CNPJ deve ter 14 dígitos para pessoa jurídica")
                                else:
                                    # Validação básica de CNPJ (soma dos dígitos)
                                    if inscricao_limpa == inscricao_limpa[0] * 14:
                                        erros.append("CNPJ não pode ter todos os dígitos iguais")
                    
                    # Validação do representante (se preenchido)
                    if representante and representante.strip() != "":
                        if len(representante.strip()) < 2:
                            erros.append("Representante deve ter pelo menos 2 caracteres")
                    
                    if erros:
                        for erro in erros:
                            st.error(erro)
                    else:
                        # Inserir cliente
                        cliente_id = db.inserir_cliente(
                            nome=nome.strip(),
                            email=email.strip(),
                            telefone=contato.strip(),
                            cpf_cnpj=inscricao.strip() if inscricao else "",
                            endereco=f"Representante: {representante.strip()}" if representante and representante.strip() else "",
                            pessoa=pessoa
                        )
                        if cliente_id:
                            st.success(f"Cliente '{nome.strip()}' cadastrado com sucesso! ID: {cliente_id}")
                        else:
                            st.error("Erro ao cadastrar cliente. Tente novamente.")
    
    with tab2:
        st.subheader("Clientes Cadastrados")
        clientes_df = db.buscar_clientes()
        
        if not clientes_df.empty:
            # Formatar CPF/CNPJ baseado no tipo de pessoa
            clientes_df['cpf_cnpj_formatado'] = clientes_df.apply(
                lambda row: formatar_cpf_cnpj(row['cpf_cnpj'], row['pessoa']), 
                axis=1
            )
            
            # Selecionar apenas as colunas necessárias
            colunas_exibicao = ['id', 'nome', 'email', 'telefone', 'cpf_cnpj_formatado', 'representante']
            clientes_df_exibicao = clientes_df[colunas_exibicao].copy()
            
            # Renomear colunas para melhor visualização
            clientes_df_exibicao = clientes_df_exibicao.rename(columns={
                'id': 'ID',
                'nome': 'Nome/Razão Social',
                'email': 'Email',
                'telefone': 'Contato',
                'cpf_cnpj_formatado': 'CPF/CNPJ',
                'representante': 'Representante'
            })
            
            st.dataframe(clientes_df_exibicao, use_container_width=True, hide_index=True)
            
            # Download dos dados
            csv = clientes_df_exibicao.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="clientes_touche.csv",
                mime="text/csv"
            )
        else:
            st.info("Nenhum cliente cadastrado ainda.")
    
    with tab3:
        st.subheader("Buscar Cliente")
        
        busca = st.text_input("Digite nome, email, CPF ou CNPJ:", placeholder="Ex: João, joao@email.com, 123.456.789-01")
        
        if busca:
            clientes_df = db.buscar_clientes()
            
            if not clientes_df.empty:
                # Filtrar resultados
                mask = (
                    clientes_df['nome'].str.contains(busca, case=False, na=False) |
                    clientes_df['email'].str.contains(busca, case=False, na=False) |
                    clientes_df['cpf_cnpj'].str.contains(busca, case=False, na=False)
                )
                
                resultados = clientes_df[mask]
                
                if not resultados.empty:
                    st.success(f"Encontrados {len(resultados)} cliente(s)")
                    
                    # Formatar CPF/CNPJ baseado no tipo de pessoa
                    resultados['cpf_cnpj_formatado'] = resultados.apply(
                        lambda row: formatar_cpf_cnpj(row['cpf_cnpj'], row['pessoa']), 
                        axis=1
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
                    "nicho": nicho,
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
                        st.write(f"**Cola Adesiva:** {resultado.get('ml_cola_adesiva', 0):.2f} ml")
                    
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
    
    orcamentos_df = db.buscar_orcamentos()
    
    if not orcamentos_df.empty:
        # Converter datas
        orcamentos_df['data_orcamento'] = pd.to_datetime(orcamentos_df['data_orcamento'])
        orcamentos_df['data_validade'] = pd.to_datetime(orcamentos_df['data_validade'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Vendas por Mês")
            orcamentos_df['mes'] = orcamentos_df['data_orcamento'].dt.strftime('%Y-%m')
            vendas_por_mes = orcamentos_df.groupby('mes')['total'].sum().reset_index()
            
            fig = px.bar(vendas_por_mes, x='mes', y='total', 
                        title='Vendas por Mês', labels={'total': 'Total (R$)', 'mes': 'Mês'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📊 Status dos Orçamentos")
            status_counts = orcamentos_df['status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        title='Distribuição por Status')
            st.plotly_chart(fig, use_container_width=True)
        
        # Top clientes
        st.subheader("🏆 Top Clientes")
        top_clientes = orcamentos_df.groupby('cliente_nome')['total'].sum().sort_values(ascending=False).head(10)
        fig = px.bar(x=top_clientes.values, y=top_clientes.index, orientation='h',
                    title='Top 10 Clientes por Valor Total', labels={'x': 'Total (R$)', 'y': 'Cliente'})
        st.plotly_chart(fig, use_container_width=True)
        
        # Estatísticas gerais
        st.subheader("📋 Estatísticas Gerais")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Orçamentos", len(orcamentos_df))
        
        with col2:
            st.metric("Valor Total", f"R$ {orcamentos_df['total'].sum():,.2f}")
        
        with col3:
            st.metric("Ticket Médio", f"R$ {orcamentos_df['total'].mean():,.2f}")
        
        with col4:
            st.metric("Orçamentos Pendentes", len(orcamentos_df[orcamentos_df['status'] == 'Pendente']))
        
    else:
        st.info("Nenhum orçamento encontrado para gerar relatórios.")

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