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

st.set_page_config(page_title="Gerador Eduten", page_icon="📊", layout="wide")

st.title("📊 Gerador de Arquivos para o Eduten")
st.markdown("Faça o upload de cada arquivo `.xls` / `.xlsx` original correspondente abaixo para gerar as planilhas processadas. Todos os processos são feitos em memória para garantir segurança e performance.")

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

if st.button("🚀 Processar Dados", type="primary", use_container_width=True):
    faltando = []
    if file_alunos is None: faltando.append("alunos.xls")
    if file_turmas is None: faltando.append("turmas.xls")
    if file_diarios is None: faltando.append("diarios.xls")
    if file_escolas is None: faltando.append("unidades_participantes.xlsx")
    if file_servidores is None: faltando.append("servidores.xlsx")
    if file_edu is None: faltando.append("@edu.xls")
    
    if len(faltando) > 0:
        st.error(f"⚠️ Por favor, envie os seguintes arquivos para continuar: {', '.join(faltando)}")
    else:
        with st.spinner("⏳ Lendo os arquivos e processando os dados... Isto pode levar alguns segundos."):
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
                st.error(f"❌ Ocorreu um erro no processamento: {str(e)}")
                st.session_state['processed_success'] = False

if st.session_state.get('processed_success', False):
    st.success("✅ Relatórios gerados com sucesso!")
    st.markdown("---")
    st.subheader("📥 Download dos Arquivos Processados")
    
    data = st.session_state['processed_data']
    
    try:
        pdf_bytes = gerar_pdf_resumo(data['matriculas'], data['turmas'], data['professores'], data.get('escolas_raw'))
        st.download_button("📄 Baixar Resumo Analítico (PDF)", data=pdf_bytes, file_name="Resumo_Analitico_EDUTEN.pdf", mime="application/pdf", type="primary", use_container_width=True)
    except Exception as e:
        st.warning(f"Não foi possível gerar o PDF de resumo: {e}")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.download_button("1. Duplicidades Antes ETL", data=df_to_excel_bytes(data['dup_antes']), file_name="duplicidades_antes_ETL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("2. Alunos Após ETL", data=df_to_excel_bytes(data['alunos_limpo']), file_name="alunos_apos_ETL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("3. Duplicidades Após ETL", data=df_to_excel_bytes(data['dup_apos']), file_name="duplicidades_apos_ETL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    with c2:
        st.download_button("4. Matrículas EDUTEN", data=df_to_excel_bytes(data['matriculas']), file_name="matriculas_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type='primary')
        st.download_button("5. Turmas EDUTEN", data=df_to_excel_bytes(data['turmas']), file_name="turmas_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type='primary')
        
    with c3:
        st.download_button("6. Diários EDUTEN", data=df_to_excel_bytes(data['diarios']), file_name="diarios_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type='primary')
        st.download_button("7. Professores EDUTEN", data=df_to_excel_bytes(data['professores']), file_name="professores_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type='primary')
        
    # We remove the balloons so they only show once, or we just leave them out to prevent annoyance on rerenders.
