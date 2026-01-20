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


CAMINHO_LOGO = "logo.png" 

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

/* Rodapé moderno */
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
    nova_data = st.date_input("Data de Conclusao", format="DD/MM/YYYY")
    submitted = st.form_submit_button("Adicionar Registro")

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
# TABELA INTERATIVA LIMPA
# ==============================
st.markdown("### 📋 Dados dos Treinamentos")
colunas_exibir = ["Colaborador", "Curso", "Data de Conclusao", "Status"]
df_tabela = df_filtrado[colunas_exibir].copy()
df_tabela["Data de Conclusao"] = pd.to_datetime(df_tabela["Data de Conclusao"], errors="coerce").dt.strftime('%d/%m/%Y')
df_tabela.reset_index(drop=True, inplace=True)

gb = GridOptionsBuilder.from_dataframe(df_tabela)
gb.configure_selection('single')
gb.configure_grid_options(
    enableRangeSelection=True,
    suppressRowClickSelection=False,
    suppressRowHoverHighlight=True
)
gb.configure_column("Colaborador", footerValue=f"Total: {len(df_tabela)}")
gb.configure_column("Status", footerValue=f"Concluídos: {df_tabela[df_tabela['Status']=='✔️ Concluído'].shape[0]} / Pendentes: {df_tabela[df_tabela['Status']=='⚠️ Sem Data'].shape[0]}")

grid_options = gb.build()

grid_response = AgGrid(
    df_tabela,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    allow_unsafe_jscode=True,
    theme="streamlit",
    fit_columns_on_grid_load=True,
    height=400
)

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
        submitted_edit = st.form_submit_button("Salvar Alterações")
        if submitted_edit:
            mask = (
                (df["Colaborador"] == registro["Colaborador"]) &
                (df["Curso"] == registro["Curso"]) &
                (df["Data de Conclusao"] == data_edit_val)
            )
            idx = df[mask].index[0]
            df.at[idx,"Colaborador"] = colab_edit
            df.at[idx,"Curso"] = curso_edit
            df.at[idx,"Data de Conclusao"] = data_edit
            df.at[idx,"Status"] = "✔️ Concluído" if data_edit else "⚠️ Sem Data"
            salvar_dados(df)
            st.success("✅ Registro atualizado com sucesso!")

    if st.button("🗑️ Excluir Registro"):
        mask = (
            (df["Colaborador"] == registro["Colaborador"]) &
            (df["Curso"] == registro["Curso"]) &
            (df["Data de Conclusao"] == data_edit_val)
        )
        idx = df[mask].index[0]
        df = df.drop(idx).reset_index(drop=True)
        salvar_dados(df)
        st.success("🗑️ Registro excluído com sucesso!")

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
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==============================
# DOWNLOAD
# ==============================
st.markdown("### 💾 Download dos Dados")
df_download = df_filtrado[colunas_exibir].copy()
df_download["Data de Conclusao"] = pd.to_datetime(df_download["Data de Conclusao"], errors="coerce").dt.strftime('%d/%m/%Y')

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