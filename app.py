import streamlit as st
import pandas as pd
from etl_processor import (
    get_duplicates_cpf, etl_alunos, gerar_matriculas_eduten, 
    remover_duplicidades, etl_turmas, etl_diarios, 
    cruzar_diarios_servidores, df_to_excel_bytes, obter_registros_novos,
    remover_professores_blacklist
)
from pdf_generator import gerar_pdf_resumo, gerar_pdf_comparativo, gerar_pdf_resumo_atualizacao

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
        file_complementador = st.file_uploader("7. complementador (exclusão facultativa)", type=["xls", "xlsx"])

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
                df_professores_base = cruzar_diarios_servidores(df_diarios_final, df_servidores_raw, df_edu_raw)
                
                # Exclusão via Complementador (Blacklist)
                if file_complementador:
                    df_comp_raw = load_data(file_complementador)
                    df_professores_final = remover_professores_blacklist(df_professores_base, df_comp_raw)
                else:
                    df_professores_final = df_professores_base
                
                # Convert all DFs to strictly Bytes during the loading spin to avoid Streamlit timeout on download click
                st.session_state['processed_bytes'] = {
                    'dup_antes': df_to_excel_bytes(df_dup_antes),
                    'dup_apos': df_to_excel_bytes(df_dup_apos),
                    'matriculas': df_to_excel_bytes(df_matriculas_final),
                    'turmas': df_to_excel_bytes(df_turmas_final),
                    'professores': df_to_excel_bytes(df_professores_final),
                }
                st.session_state['pdf_bytes'] = gerar_pdf_resumo(df_matriculas_final, df_turmas_final, df_professores_final, df_escolas_raw)
                st.session_state['pdf_comparativo_bytes'] = gerar_pdf_comparativo(df_turmas_final, df_alunos_limpo, df_matriculas_final, df_dup_apos)
                st.session_state['processed_success'] = True

            except Exception as e:
                st.error(f"Ocorreu um erro no processamento: {str(e)}")
                st.session_state['processed_success'] = False

if st.session_state.get('processed_success', False):
    st.success("Relatórios gerados com sucesso!")
    st.markdown("---")
    st.subheader("Download dos Arquivos Processados")
    
    col_pdf1, col_pdf2 = st.columns(2)
    with col_pdf1:
        try:
            st.download_button("Baixar Resumo Analítico", data=st.session_state['pdf_bytes'], file_name="Resumo_Analitico_EDUTEN.pdf", mime="application/pdf", width='stretch')
        except Exception as e:
            st.warning(f"Não foi possível gerar o PDF de resumo: {e}")
            
    with col_pdf2:
        try:
            st.download_button("Baixar Relatório de Divergências por Duplicidades", data=st.session_state['pdf_comparativo_bytes'], file_name="Relatório_de_Duplicidades_EDUTEN.pdf", mime="application/pdf", width='stretch')
        except Exception as e:
            st.warning(f"Não foi possível gerar o PDF comparativo: {e}")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Organização baseada no fluxo (imagem 2)
    c1, c2, c3 = st.columns(3)
    
    byte_dict = st.session_state['processed_bytes']
    
    with c1:
        st.markdown("**Arquivos de Envio ao Eduten**")
        st.download_button("Relação Final de Matrículas", data=byte_dict['matriculas'], file_name="matriculas_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Relação Final de Professores", data=byte_dict['professores'], file_name="professores_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    with c2:
        st.markdown("**Tratamento de Duplicidades**")
        st.download_button("Duplicidades Geral", data=byte_dict['dup_antes'], file_name="duplicidades_antes_ETL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("Duplicidades participantes do Eduten", data=byte_dict['dup_apos'], file_name="duplicidades_apos_ETL.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
    with c3:
        st.markdown("**Materiais de Validação**")
        st.download_button("Relação de Turmas para o Eduten", data=byte_dict['turmas'], file_name="turmas_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# SEÇÃO: ATUALIZAÇÃO DA BASE DE DADOS
st.markdown("---")
st.subheader("Atualização da Base de Dados")
st.markdown("Faça o upload dos arquivos gerados anteriormente e da nova remessa processada para detectar e exportar **apenas as inscrições novas** que não existiam na base antiga.")

with st.container():
    col_up_1, col_up_2 = st.columns(2)
    with col_up_1:
        st.markdown("**Matrículas EDUTEN**")
        file_m_antes = st.file_uploader("Arquivo (Antes)", type=['xlsx'], key='mat_antes', help="O arquivo exportado de Relação Final de Matrículas anterior à atualização.")
        file_m_depois = st.file_uploader("Arquivo (Depois)", type=['xlsx'], key='mat_depois', help="O arquivo Relação Final de Matrículas novo gerado agora com mais pessoas.")
        
    with col_up_2:
        st.markdown("**Professores EDUTEN**")
        file_p_antes = st.file_uploader("Arquivo (Antes)", type=['xlsx'], key='prof_antes', help="A Relação Final de Professores antiga.")
        file_p_depois = st.file_uploader("Arquivo (Depois)", type=['xlsx'], key='prof_depois', help="A Relação Final de Professores gerada agora com mais pessoas.")
        
    if st.button("Processar Atualizações de Base", key='btn_atualizar'):
        with st.spinner("Comparando as bases de dados..."):
            try:
                df_m_antes = load_data(file_m_antes) if file_m_antes else None
                df_m_depois = load_data(file_m_depois) if file_m_depois else None
                df_p_antes = load_data(file_p_antes) if file_p_antes else None
                df_p_depois = load_data(file_p_depois) if file_p_depois else None
                
                df_novas_matriculas = obter_registros_novos(df_m_antes, df_m_depois)
                df_novos_professores = obter_registros_novos(df_p_antes, df_p_depois)
                
                st.session_state['bytes_atualizacao_mat'] = df_to_excel_bytes(df_novas_matriculas) if not df_novas_matriculas.empty else None
                st.session_state['bytes_atualizacao_prof'] = df_to_excel_bytes(df_novos_professores) if not df_novos_professores.empty else None
                st.session_state['bytes_pdf_atualizacao'] = gerar_pdf_resumo_atualizacao(df_novas_matriculas, df_novos_professores)
                st.session_state['atualizacao_processada'] = True
                st.success("Matrículas e dados comparados com sucesso!")
            except Exception as e:
                st.error(f"Ocorreu um erro na comparação iterativa: {e}")
                
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### Downloads das Atualizações Geradas")
    cp1, cp2, cp3 = st.columns(3)
    
    with cp1:
        if st.session_state.get('atualizacao_processada') and st.session_state.get('bytes_pdf_atualizacao'):
            st.download_button("Baixar Resumo Analítico da Atualização", data=st.session_state['bytes_pdf_atualizacao'], file_name="Resumo_Analitico_Atualizacao.pdf", mime="application/pdf", use_container_width=True)
        else:
            if st.button("Baixar Resumo Analítico da Atualização", use_container_width=True, key='btn_warn_pdf'):
                if not st.session_state.get('atualizacao_processada'):
                    st.info("Realize o processamento das atualizações para gerar o PDF.")
                else:
                    st.warning("Resumo não disponível (sem dados para atualizar).")
    
    with cp2:
        if st.session_state.get('atualizacao_processada') and st.session_state.get('bytes_atualizacao_mat'):
            st.download_button("Baixar atualizacao_matriculas_EDUTEN.xlsx", data=st.session_state['bytes_atualizacao_mat'], file_name="atualizacao_matriculas_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            if st.button("Baixar atualizacao_matriculas_EDUTEN.xlsx", use_container_width=True, key='btn_warn_mat'):
                if not st.session_state.get('atualizacao_processada'):
                    st.info("Realize o processamento das atualizações primeiro.")
                else:
                    st.warning("Não foram detectadas novas matrículas nesta atualização.")
    
    with cp3:
        if st.session_state.get('atualizacao_processada') and st.session_state.get('bytes_atualizacao_prof'):
            st.download_button("Baixar atualizacao_professores_EDUTEN.xlsx", data=st.session_state['bytes_atualizacao_prof'], file_name="atualizacao_professores_EDUTEN.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            if st.button("Baixar atualizacao_professores_EDUTEN.xlsx", use_container_width=True, key='btn_warn_prof'):
                if not st.session_state.get('atualizacao_processada'):
                    st.info("Realize o processamento das atualizações primeiro.")
                else:
                    st.warning("Não foram detectados novos professores nesta atualização.")

# Rodapé do Projeto
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>Desenvolvido pela Gerência de Administração de Sistemas em TI - Versão 1.1</p>", unsafe_allow_html=True)
