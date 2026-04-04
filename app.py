import streamlit as st
import pandas as pd
from etl_processor import (
    get_duplicates_cpf, etl_alunos, gerar_matriculas_eduten, 
    remover_duplicidades, etl_turmas, etl_diarios, 
    cruzar_diarios_servidores, df_to_excel_bytes
)
from pdf_generator import gerar_pdf_resumo

def load_data(file):
    if file.name.lower().endswith('.csv'):
        # Tenta ler com separador ponto-e-vírgula comum no Brasil
        try:
            return pd.read_csv(file, sep=';', encoding='utf-8')
        except UnicodeDecodeError:
            file.seek(0)
            return pd.read_csv(file, sep=';', encoding='latin1')
    else:
        return pd.read_excel(file)

st.set_page_config(page_title="Gerador Eduten", layout="wide")

st.markdown("""
    <style>
    /* Styling buttons to be blue with rounded edges */
    div.stButton > button:first-child {
        background-color: #0056b3 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        height: auto !important;
        font-weight: 600 !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #004494 !important;
        border: none !important;
        color: white !important;
    }
    /* Styling download buttons exactly the same */
    div.stDownloadButton > button:first-child {
        background-color: #0056b3 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
    }
    div.stDownloadButton > button:first-child:hover {
        background-color: #004494 !important;
        border: none !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

col_titulo, col_btn = st.columns([8, 2])
with col_titulo:
    st.title("Gerador de Arquivos - EDUTEN")

with col_btn:
    st.markdown("<br>", unsafe_allow_html=True) # Alinhamento espaçado vertical
    try:
        with open("documentacao.pdf", "rb") as pdf_file:
            st.download_button("Documentação", data=pdf_file.read(), file_name="documentacao.pdf", mime="application/pdf", width="stretch")
    except FileNotFoundError:
        st.download_button("Documentação", data=b"", file_name="documentacao.pdf", mime="application/pdf", disabled=True, width="stretch", help="O arquivo documentacao.pdf não está na pasta.")

st.markdown("Faça o upload de cada arquivo original correspondente abaixo para gerar as planilhas processadas. Todos os processos são feitos em memória para garantir segurança e performance.")

with st.expander("📁 Upload de Arquivos de Entrada", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Base Escolar")
        file_alunos = st.file_uploader("1. alunos (xls, xlsx ou csv)", type=["xls", "xlsx", "csv"])
        file_turmas = st.file_uploader("2. turmas (xls, xlsx ou csv)", type=["xls", "xlsx", "csv"])
        file_diarios = st.file_uploader("3. diarios (xls, xlsx ou csv)", type=["xls", "xlsx", "csv"])
    with col2:
        st.subheader("Servidores e Cadastros")
        file_escolas = st.file_uploader("4. unidades_participantes", type=["xls", "xlsx", "csv"])
        file_servidores = st.file_uploader("5. servidores", type=["xls", "xlsx", "csv"])
        file_edu = st.file_uploader("6. @edu", type=["xls", "xlsx", "csv"])

if st.button("Processar Dados", width='stretch'):
    faltando = []
    if file_alunos is None: faltando.append("alunos.xls")
    if file_turmas is None: faltando.append("turmas.xls")
    if file_diarios is None: faltando.append("diarios.xls")
    if file_escolas is None: faltando.append("unidades_participantes.xlsx")
    if file_servidores is None: faltando.append("servidores.xlsx")
    if file_edu is None: faltando.append("@edu.xls")
    
    if len(faltando) > 0:
        st.error(f"Por favor, envie os seguintes arquivos para continuar: {', '.join(faltando)}")
    else:
        with st.spinner("Lendo os arquivos e processando os dados... Isto pode levar alguns segundos."):
            try:
                # Reading input DataFrames dynamically (CSV or XLS/XLSX)
                df_alunos_raw = load_data(file_alunos)
                df_turmas_raw = load_data(file_turmas)
                df_diarios_raw = load_data(file_diarios)
                df_escolas_raw = load_data(file_escolas)
                df_servidores_raw = load_data(file_servidores)
                df_edu_raw = load_data(file_edu)

                # Flow 1: Quality Control - Duplicates before ETL
                df_dup_antes = get_duplicates_cpf(df_alunos_raw)
                
                # Flow 2: ETL Alunos
                df_alunos_limpo = etl_alunos(df_alunos_raw)
                
                # Flow 3: Quality Control - Duplicates after ETL
                df_dup_apos = get_duplicates_cpf(df_alunos_limpo)
                
                # Flow 4: Matriculas
                df_matriculas = gerar_matriculas_eduten(df_alunos_limpo, df_escolas_raw)
                
                # Flow 5: Remove duplicates from Matriculas
                df_matriculas_final = remover_duplicidades(df_matriculas, df_dup_apos)
                
                # Flow 6: ETL Turmas
                df_turmas_final = etl_turmas(df_turmas_raw, df_escolas_raw)
                
                # Flow 7: ETL Diarios
                df_diarios_final = etl_diarios(df_diarios_raw, df_escolas_raw)
                
                # Flow 8: Professores
                df_professores_final = cruzar_diarios_servidores(df_diarios_final, df_servidores_raw, df_edu_raw)
                
                # Store the results in session state so they don't disappear on button click
                st.session_state['processed_data'] = {
                    'dup_antes': df_dup_antes,
                    'alunos_limpo': df_alunos_limpo,
                    'dup_apos': df_dup_apos,
                    'matriculas': df_matriculas_final,
                    'turmas': df_turmas_final,
                    'diarios': df_diarios_final,
                    'professores': df_professores_final,
                    'escolas_raw': df_escolas_raw
                }
                st.session_state['processed_success'] = True

            except Exception as e:
                st.error(f"Ocorreu um erro no processamento: {str(e)}")
                st.session_state['processed_success'] = False

if st.session_state.get('processed_success', False):
    st.success("Relatórios gerados com sucesso!")
    st.markdown("---")
    st.subheader("Download dos Arquivos Processados")
    
    data = st.session_state['processed_data']
    
    # Resumo Analítico isolado no topo
    try:
        pdf_bytes = gerar_pdf_resumo(data['matriculas'], data['turmas'], data['professores'], data.get('escolas_raw'))
        st.download_button("Baixar Resumo Analítico (PDF)", data=pdf_bytes, file_name="Resumo_Analitico_EDUTEN.pdf", mime="application/pdf", width='stretch')
    except Exception as e:
        st.warning(f"Não foi possível gerar o PDF de resumo: {e}")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Organização baseada no fluxo (imagem 2)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("**Tratamento de Duplicidades (ETL)**")
        st.download_button("Duplicidades Antes ETL", data=df_to_excel_bytes(data['dup_antes']), file_name="duplicidades_antes_ETL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Duplicidades Após ETL", data=df_to_excel_bytes(data['dup_apos']), file_name="duplicidades_apos_ETL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    with c2:
        st.markdown("**Arquivos de Envio ao EDUTEN**")
        st.download_button("Relação Final de Matrículas", data=df_to_excel_bytes(data['matriculas']), file_name="matriculas_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Professores Participantes", data=df_to_excel_bytes(data['professores']), file_name="professores_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    with c3:
        st.markdown("**Materiais de Validação**")
        st.download_button("Turmas para Conferência dos Dados", data=df_to_excel_bytes(data['turmas']), file_name="turmas_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Arquivos de Diários", data=df_to_excel_bytes(data['diarios']), file_name="diarios_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Alunos Após ETL (Base Limpa)", data=df_to_excel_bytes(data['alunos_limpo']), file_name="alunos_apos_ETL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Rodapé do Projeto
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Desenvolvido pela Gerência de Administração de Sistemas em TI - Versão 1.1</p>", unsafe_allow_html=True)
