import streamlit as st
import pandas as pd
from datetime import datetime
import os
import unidecode
import plotly.express as px
import io
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode 

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Registro de Treinamentos",
    layout="wide"
)

CAMINHO_PLANILHA = "treinamentos.xlsx"
COLUNAS_PADRAO = ["Colaborador", "Curso", "Data de Conclusao"]

# ATUALIZADO: Usando o nome do arquivo de imagem carregado para exibição do logo.
# Certifique-se de que este arquivo ('image_59eaba.png') está na mesma pasta do script.
CAMINHO_LOGO = "image_59eaba.png" 

# ==============================
# ESTILO CSS
# ==============================
st.markdown("""
<style>
/* Estilização para o fundo principal e texto */
.stApp {
    background-color: #002147; /* Azul Escuro */
    color: white;
    font-family: 'Segoe UI', sans-serif;
}
h1 {
    text-align: center;
    font-size: 28px;
    color: white;
    margin-bottom: 5px;
}
/* Estilo para o footer fixo na parte inferior */
.footer {
    position: fixed;
    bottom: 10px;
    width: 95%;
    margin: 0 2.5%;
    background-color: #001f4d;  
    color: #ffffff;
    text-align: center;
    padding: 6px 0;
    font-size: 13px;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.5);
    opacity: 0.9;
    z-index: 1000;
}
/* Altera o estilo dos widgets Streamlit (Headers, Inputs) para harmonizar */
div.stSelectbox > label, div.stTextInput > label, div.stDateInput > label {
    font-weight: bold;
    color: #ADD8E6; /* Azul Claro para os rótulos */
}
</style>
""", unsafe_allow_html=True)

# ==============================
# FUNÇÕES
# ==============================
# Adicionado @st.cache_data para otimizar o carregamento de dados (boa prática do Streamlit)
@st.cache_data
def carregar_dados(caminho):
    """Carrega o DataFrame do Excel e padroniza as colunas."""
    if not os.path.exists(caminho):
        df = pd.DataFrame(columns=COLUNAS_PADRAO)
        df.to_excel(caminho, index=False)

    df = pd.read_excel(caminho)
    
    # Padronização e mapeamento de colunas
    df.columns = [unidecode.unidecode(str(c).strip().lower()) for c in df.columns]

    mapeamento = {
        "colaborador": "Colaborador",
        "funcionario": "Colaborador",
        "nome": "Colaborador",
        "curso": "Curso",
        "treinamento": "Curso",
        "data de conclusao": "Data de Conclusao",
        "dados de conclusao": "Data de Conclusao",
        "data conclusao": "Data de Conclusao",
        "data de conclusão": "Data de Conclusao",
        "dados de conclusão": "Data de Conclusao",
    }
    # Aplica o mapeamento e mantém o nome original se não encontrado
    df.columns = [mapeamento.get(c, c) for c in df.columns]

    # Garante que as colunas padrão existem, adicionando-as se necessário
    for col in COLUNAS_PADRAO:
        if col not in df.columns:
            df[col] = ''
            
    # Converte a data para o tipo 'date' do Python
    df["Data de Conclusao"] = pd.to_datetime(df["Data de Conclusao"], errors="coerce").dt.date
    df["Status"] = df["Data de Conclusao"].apply(lambda x: "✔️ Concluído" if pd.notna(x) else "⚠️ Sem Data")
    
    return df[COLUNAS_PADRAO + ["Status"]] # Retorna apenas as colunas relevantes

def salvar_dados(df):
    """Salva o DataFrame no arquivo Excel."""
    df.to_excel(CAMINHO_PLANILHA, index=False)
    # Após salvar, força o recarregamento dos dados em cache
    st.cache_data.clear()

def aplicar_filtros(df, colaborador, curso, status):
    """Aplica os filtros selecionados ao DataFrame."""
    if colaborador:
        df = df[df["Colaborador"].str.contains(colaborador, case=False, na=False)]
    if curso:
        df = df[df["Curso"].str.contains(curso, case=False, na=False)]
    if status != "Todos":
        df = df[df["Status"] == status]
    return df

# ==============================
# CARREGAR DADOS
# ==============================
# Garante que o DataFrame seja recarregado apenas se o estado mudar
if 'df' not in st.session_state:
    st.session_state['df'] = carregar_dados(CAMINHO_PLANILHA)

df = st.session_state['df']

# ==============================
# CABEÇALHO COM LOGO
# ==============================
col1, col2, col3 = st.columns([1,6,1])
with col1: st.write("")
with col2:
    # CORREÇÃO: Tratamento de erro mais abrangente para evitar o crash do app
    # devido a 'MediaFileStorageError' (que não é um FileNotFoundError).
    # Isso garante que o restante do app seja carregado, mesmo que o logo falhe.
    try:
        st.image(CAMINHO_LOGO, width=180) 
    except Exception as e:
        # Exibe um erro amigável ao usuário.
        st.warning(f"⚠️ Aviso: Não foi possível carregar o logo ('{CAMINHO_LOGO}'). Verifique se o arquivo está no diretório correto do seu repositório.")
    
    st.markdown("<h1>Registro de Treinamentos</h1>", unsafe_allow_html=True)
with col3: st.write("")
st.markdown("---")

# ==============================
# FORMULÁRIO - ADICIONAR REGISTRO
# ==============================
st.markdown("### ➕ Adicionar Novo Registro")
with st.form("form_incluir"):
    novo_colaborador = st.text_input("Colaborador")
    novo_curso = st.text_input("Curso")
    # Define a data atual como padrão se nada for selecionado
    nova_data = st.date_input("Data de Conclusao", value=datetime.today().date(), format="DD/MM/YYYY") 
    
    submitted = st.form_submit_button("Adicionar Registro", type="primary")
    
    if submitted:
        if not novo_colaborador or not novo_curso:
            st.error("⚠️ Preencha Colaborador e Curso antes de adicionar.")
        else:
            novo_registro = {
                "Colaborador": novo_colaborador.strip(),
                "Curso": novo_curso.strip(),
                "Data de Conclusao": nova_data,
                "Status": "✔️ Concluído" if nova_data else "⚠️ Sem Data"
            }
            # Atualiza o DataFrame na sessão e salva no arquivo
            st.session_state['df'] = pd.concat([df, pd.DataFrame([novo_registro])], ignore_index=True)
            salvar_dados(st.session_state['df'])
            st.success("✅ Registro adicionado com sucesso!")
            st.rerun()  # Recarrega o script Streamlit para refletir a mudança

st.markdown("---")

# ==============================
# FILTROS
# ==============================
st.markdown("### 🔍 Filtros")
colf1, colf2, colf3 = st.columns(3)
filtro_colaborador = colf1.text_input("Filtrar por Colaborador")
filtro_curso = colf2.text_input("Filtrar por Curso")
status_opcoes = ["Todos", "✔️ Concluído", "⚠️ Sem Data"]
filtro_status = colf3.selectbox("Status", status_opcoes)

df_filtrado = aplicar_filtros(df, filtro_colaborador, filtro_curso, filtro_status)

# ==============================
# RESUMO
# ==============================
colr1, colr2, colr3 = st.columns(3)
colr1.metric("Total", len(df_filtrado))
colr2.metric("Concluídos", df_filtrado[df_filtrado["Status"]=="✔️ Concluído"].shape[0])
colr3.metric("Pendentes", df_filtrado[df_filtrado["Status"]=="⚠️ Sem Data"].shape[0])
st.markdown("---")

# ==============================
# FUNÇÃO PARA RENDER TABELA
# ==============================
# CORREÇÃO 2: Removidos os placeholders desnecessários para a exibição sequencial de elementos.
# A tabela e o gráfico agora serão renderizados na ordem em que aparecem no código.

def render_tabela(df_filtrado):
    """Renderiza a tabela usando AgGrid."""
    df_tabela = df_filtrado.copy()
    
    # Formata a data para exibição (string)
    df_tabela["Data de Conclusao"] = pd.to_datetime(df_tabela["Data de Conclusao"], errors="coerce").dt.strftime('%d/%m/%Y').fillna('')
    df_tabela.reset_index(drop=True, inplace=True)

    gb = GridOptionsBuilder.from_dataframe(df_tabela)
    # Configuração de seleção e rodapé
    gb.configure_selection('single', use_checkbox=True) # Adiciona checkbox para melhor seleção
    
    # Customização do rodapé (Footer)
    total_registros = len(df_tabela)
    concluidos = df_tabela[df_tabela['Status']=='✔️ Concluído'].shape[0]
    pendentes = df_tabela[df_tabela['Status']=='⚠️ Sem Data'].shape[0]
    
    gb.configure_column("Colaborador", footerValue=f"Total: {total_registros}")
    gb.configure_column("Status", footerValue=f"C: {concluidos} / P: {pendentes}")
    
    grid_options = gb.build()

    return AgGrid(
        df_tabela,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED, # Modo mais eficiente
        allow_unsafe_jscode=True,
        theme="streamlit",
        fit_columns_on_grid_load=True,
        height=400,
        data_return_mode='AS_INPUT',
        enable_enterprise_modules=False
    )

st.markdown("### 📊 Dados dos Treinamentos") # Título para a tabela
grid_response = render_tabela(df_filtrado)
selected = grid_response['selected_rows']

# ==============================
# EDITAR / EXCLUIR REGISTRO
# ==============================
if selected:
    registro = selected[0]
    
    # A data do AgGrid vem como string formatada dd/mm/yyyy ou string vazia
    data_edit_str = registro.get("Data de Conclusao", "")

    # Conversão da data do registro selecionado para objeto date para preencher o date_input
    if data_edit_str:
        try:
            data_edit_val = datetime.strptime(data_edit_str, "%d/%m/%Y").date()
            # Esta é a data que existia no DF original (como objeto date)
            # Para o `df.at[idx,...]` e `df.drop(idx)` precisamos encontrar o índice no DF original.
            # O DF original (`df`) tem a data como objeto `date` ou `pd.NaT`.
            data_para_comparacao = data_edit_val
        except ValueError:
            # Caso raro de string inválida, tratamos como None (Sem Data)
            data_edit_val = datetime.today().date()
            data_para_comparacao = pd.NaT
    else:
        # Se for Sem Data/vazio, use a data de hoje como padrão para edição
        data_edit_val = datetime.today().date()
        data_para_comparacao = pd.NaT # Representa NaN/nulo no DF original

    st.markdown("#### ✏️ Editar Registro Selecionado")
    with st.form("form_editar"):
        # Preenche os campos com os valores selecionados do AgGrid
        colab_edit = st.text_input("Colaborador", value=registro.get("Colaborador",""))
        curso_edit = st.text_input("Curso", value=registro.get("Curso",""))
        
        # O valor inicial do date_input é o valor da linha selecionada
        data_edit = st.date_input("Data de Conclusao", value=data_edit_val, format="DD/MM/YYYY")
        
        submitted_edit = st.form_submit_button("Salvar Alterações", type="primary")
        
        # --- LÓGICA DE EDIÇÃO/ATUALIZAÇÃO ---
        # Buscamos o índice original usando os valores da linha selecionada antes da edição.
        
        # A máscara precisa lidar com valores nulos (NaT) na coluna Data de Conclusao
        if pd.isna(data_para_comparacao):
            mask_data = df["Data de Conclusao"].isna()
        else:
            mask_data = (df["Data de Conclusao"] == data_para_comparacao)

        mask_original = (
            (df["Colaborador"] == registro["Colaborador"]) &
            (df["Curso"] == registro["Curso"]) &
            mask_data
        )
        
        indices = df[mask_original].index
        
        if submitted_edit and len(indices) == 1:
            idx = indices[0]
            
            # Atualiza os valores no DataFrame de Sessão
            st.session_state['df'].at[idx,"Colaborador"] = colab_edit
            st.session_state['df'].at[idx,"Curso"] = curso_edit
            st.session_state['df'].at[idx,"Data de Conclusao"] = data_edit
            st.session_state['df'].at[idx,"Status"] = "✔️ Concluído" if data_edit else "⚠️ Sem Data"
            
            salvar_dados(st.session_state['df'])
            st.success("✅ Registro atualizado com sucesso!")
            st.rerun()
        elif submitted_edit:
             st.error("⚠️ Erro ao encontrar o registro para edição. Tente novamente.")

    if st.button("🗑️ Excluir Registro"):
        # A máscara é a mesma usada acima para identificar o registro original
        indices = df[mask_original].index
        
        if len(indices) == 1:
            idx = indices[0]
            # Exclui a linha e salva o novo DataFrame na sessão
            st.session_state['df'] = df.drop(idx).reset_index(drop=True)
            salvar_dados(st.session_state['df'])
            st.success("🗑️ Registro excluído com sucesso!")
            st.rerun()
        else:
            st.error("⚠️ Erro ao encontrar o registro para exclusão. Tente novamente.")

st.markdown("---")

# ==============================
# GRÁFICOS DINÂMICOS
# ==============================
st.markdown("### 📈 Gráficos Dinâmicos") # Título para o gráfico
opcoes_colunas = ["Colaborador", "Curso", "Data de Conclusao"]
col_graf1, col_graf2 = st.columns(2)
coluna_selecionada = col_graf1.selectbox("Coluna para visualizar", options=opcoes_colunas)
tipo_grafico = col_graf2.radio("Tipo de gráfico", ["Barras","Pizza","Linha"], horizontal=True)

if coluna_selecionada in df_filtrado.columns:
    dados = df_filtrado.dropna(subset=[coluna_selecionada]).copy()
    if "data" in coluna_selecionada.lower():
        dados["Data de Conclusao"] = pd.to_datetime(dados["Data de Conclusao"], errors="coerce")
        contagem = dados.groupby("Data de Conclusao").size().reset_index(name="Total")
        contagem["Data_de_Conclusao_Str"] = contagem["Data de Conclusao"].dt.strftime("%d/%m/%Y")
        eixo_x = "Data_de_Conclusao_Str"
    else:
        contagem = dados[coluna_selecionada].value_counts().reset_index()
        contagem.columns = [coluna_selecionada, "Total"]
        eixo_x = contagem.columns[0]

    if tipo_grafico == "Barras":
        fig = px.bar(contagem, x=eixo_x, y="Total", text_auto=True, color="Total", 
                     color_continuous_scale=px.colors.sequential.Agsunset)
    elif tipo_grafico == "Pizza":
        fig = px.pie(contagem.head(10), names=eixo_x, values="Total", hole=0.4)
    else:
        fig = px.line(contagem, x=eixo_x, y="Total", markers=True)

    fig.update_layout(xaxis_title="", yaxis_title="Total", template="plotly_dark")
    # Tenta melhorar a apresentação do eixo X para datas
    if "data" in coluna_selecionada.lower() and tipo_grafico in ["Barras", "Linha"]:
        fig.update_xaxes(tickangle=45)
    
    # CORREÇÃO 3: Usando st.plotly_chart diretamente, sem o placeholder, e na ordem correta.
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==============================
# DOWNLOAD
# ==============================
st.markdown("### 💾 Download dos Dados")
df_download = df_filtrado[["Colaborador","Curso","Data de Conclusao","Status"]].copy()
# Mantém a data no formato 'YYYY-MM-DD' para CSV/Excel para que seja reconhecida como data
df_download["Data de Conclusao"] = pd.to_datetime(df_download["Data de Conclusao"], errors="coerce").dt.strftime('%Y-%m-%d').fillna('')

col_down1, col_down2 = st.columns(2)

with col_down1:
    st.download_button(
        label="📥 Baixar CSV",
        data=df_download.to_csv(index=False).encode("utf-8"),
        file_name=f"treinamentos_filtrado_{datetime.now().strftime('%d%m%Y_%H%M')}.csv",
        mime="text/csv"
    )

with col_down2:
    buffer = io.BytesIO()
    # Remove a coluna Status do Excel de download
    df_download.drop(columns=["Status"]).to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="📥 Baixar Excel",
        data=buffer,
        file_name=f"treinamentos_filtrado_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==============================
# RODAPÉ
# ==============================
st.markdown("""
<div class="footer">
<span>🖥️ Monitoramento Infotec | RT - Nathália Brum | © 2025</span>
</div>
""", unsafe_allow_html=True)
