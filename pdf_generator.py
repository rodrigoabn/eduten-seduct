import io
from fpdf import FPDF
import pandas as pd
from datetime import datetime

class PDFResumo(FPDF):
    def header(self):
        try:
            self.image('brasao.png', 10, 8, 20)
        except Exception:
            pass
        self.set_font('helvetica', 'B', 12)
        self.cell(25)
        self.cell(0, 6, "Secretaria Municipal de Educação, Ciência e Tecnologia", ln=1)
        self.set_font('helvetica', '', 11)
        self.cell(25)
        self.cell(0, 5, "Gerência de Administração de Sistemas em TI", ln=1)
        self.set_font('helvetica', 'I', 11)
        self.cell(25)
        # Handle unicode manually if latin-1 encodes fail but FPDF2 handles utf-8
        self.cell(0, 5, "Resumo analítico dos dados para o EDUTEN", ln=1)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        
        meses = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        hoje = datetime.now()
        
        w = self.epw / 3
        
        self.cell(w, 10, "Contato: admsistemas@edu.campos.rj.gov.br", align='L')
        self.cell(w, 10, str(self.page_no()), align='C')
        self.cell(w, 10, f"Campos dos Goytacazes, {hoje.day} de {meses[hoje.month]} de {hoje.year}", align='R')

def gerar_pdf_resumo(df_matriculas, df_turmas, df_professores, df_escolas=None):
    pdf = PDFResumo()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    df_matriculas.columns = df_matriculas.columns.str.strip()
    col_ue_mat = 'Unidade Escolar' if 'Unidade Escolar' in df_matriculas.columns else df_matriculas.columns[0]
    
    df_turmas.columns = df_turmas.columns.str.strip()
    col_ue_tur = 'UNIDADES ESCOLARES' if 'UNIDADES ESCOLARES' in df_turmas.columns else df_turmas.columns[0]
    
    col_ue_prof = 'Unidade Escolar' if 'Unidade Escolar' in df_professores.columns else df_professores.columns[0]
    
    turmas_por_escola = df_turmas.groupby(col_ue_tur).size().to_dict()
    alunos_por_escola = df_matriculas.groupby(col_ue_mat).size().to_dict()
    if 'Matrícula' in df_professores.columns:
        prof_por_escola = df_professores.groupby(col_ue_prof)['Matrícula'].nunique().to_dict()
    else:
        prof_por_escola = df_professores.groupby(col_ue_prof).size().to_dict()
    
    # Getting accurate list of all schools from the provided 'unidades_participantes.xlsx'
    if df_escolas is not None and 'Nome SUAP' in df_escolas.columns:
        escolas_set = set(df_escolas['Nome SUAP'].astype(str).str.strip().tolist())
    else:
        escolas_set = set(turmas_por_escola.keys()).union(set(alunos_por_escola.keys())).union(set(prof_por_escola.keys()))
        
    escolas_lista = sorted([str(e) for e in escolas_set if str(e).lower() != 'nan' and str(e).strip() != ''])
    
    total_ue = len(escolas_lista)
    total_turmas = len(df_turmas)
    total_professores = df_professores['Matrícula'].nunique() if 'Matrícula' in df_professores.columns else len(df_professores)
    total_alunos = len(df_matriculas)
    
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "1. Resumo Quantitativo Geral", ln=1)
    pdf.set_font("helvetica", '', 11)
    
    pdf.cell(0, 6, f"Total de Unidades Escolares: {total_ue}", ln=1)
    pdf.cell(0, 6, f"Total de Turmas: {total_turmas}", ln=1)
    pdf.cell(0, 6, f"Total de Professores: {total_professores}", ln=1)
    pdf.cell(0, 6, f"Total de Matrículas: {total_alunos}", ln=1)
    pdf.ln(5)
    
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "2. Unidades sem dados informados", ln=1)
    
    sem_turmas = [e for e in escolas_lista if turmas_por_escola.get(e, 0) == 0]
    sem_alunos = [e for e in escolas_lista if alunos_por_escola.get(e, 0) == 0]
    sem_profs = [e for e in escolas_lista if prof_por_escola.get(e, 0) == 0]
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(0, 6, "Escolas sem Turmas informadas:", ln=1)
    pdf.set_font("helvetica", '', 10)
    if sem_turmas:
        pdf.multi_cell(0, 5, ", ".join(sem_turmas))
    else:
        pdf.cell(0, 5, "Nenhuma.", ln=1)
    
    pdf.ln(2)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(0, 6, "Escolas sem Alunos informados:", ln=1)
    pdf.set_font("helvetica", '', 10)
    if sem_alunos:
        pdf.multi_cell(0, 5, ", ".join(sem_alunos))
    else:
        pdf.cell(0, 5, "Nenhuma.", ln=1)
        
    pdf.ln(2)
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(0, 6, "Escolas sem Professores informados:", ln=1)
    pdf.set_font("helvetica", '', 10)
    if sem_profs:
        pdf.multi_cell(0, 5, ", ".join(sem_profs))
    else:
        pdf.cell(0, 5, "Nenhuma.", ln=1)
    
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "3. Relação de Unidades Escolares", ln=1)
    pdf.set_font("helvetica", '', 11)
    
    pdf.set_font("helvetica", 'B', 10)
    pdf.cell(10, 8, "#", border=1, align='C')
    pdf.cell(85, 8, "Unidade Escolar", border=1)
    pdf.cell(30, 8, "Turmas", border=1, align='C')
    pdf.cell(35, 8, "Professores", border=1, align='C')
    pdf.cell(30, 8, "Alunos", border=1, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", '', 9)
    for i, escola in enumerate(escolas_lista, start=1):
        t_turmas = turmas_por_escola.get(escola, 0)
        t_profs = prof_por_escola.get(escola, 0)
        t_alunos = alunos_por_escola.get(escola, 0)
        
        nome_escola = escola[:42] + "..." if len(escola) > 42 else escola
        pdf.cell(10, 7, str(i), border=1, align='C')
        pdf.cell(85, 7, nome_escola, border=1)
        pdf.cell(30, 7, str(t_turmas), border=1, align='C')
        pdf.cell(35, 7, str(t_profs), border=1, align='C')
        pdf.cell(30, 7, str(t_alunos), border=1, align='C')
        pdf.ln()
        
    return bytes(pdf.output())

def gerar_pdf_comparativo(df_turmas, df_alunos_limpo, df_matriculas_final, df_dup_apos=None):
    pdf = PDFResumo()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "Relatório Informativo de Divergências por Duplicidades", ln=1, align='C')
    pdf.set_font("helvetica", '', 11)
    pdf.multi_cell(0, 6, "Este relatorio lista as turmas aprovadas no EDUTEN que sofreram baixa na sua contagem de matriculas como resultado das exclusoes geradas pelo tratamento de duplicidades.")
    pdf.ln(5)
    
    import pandas as pd
    
    col_ue_tur = 'UNIDADES ESCOLARES' if 'UNIDADES ESCOLARES' in df_turmas.columns else df_turmas.columns[0]
    col_cod_tur = 'CODIGO' if 'CODIGO' in df_turmas.columns else df_turmas.columns[1]
    
    valid_turmas = df_turmas[[col_ue_tur, col_cod_tur]].drop_duplicates()
    valid_turmas.columns = ['Unidade Escolar', 'Turma']
    valid_turmas['Unidade Escolar'] = valid_turmas['Unidade Escolar'].astype(str).str.strip()
    valid_turmas['Turma'] = valid_turmas['Turma'].astype(str).str.strip()
    
    col_ue_alu = 'Unidade Escolar' if 'Unidade Escolar' in df_alunos_limpo.columns else df_alunos_limpo.columns[0]
    col_cod_alu = 'Código da Turma Suap' if 'Código da Turma Suap' in df_alunos_limpo.columns else df_alunos_limpo.columns[1]
    df_alu = df_alunos_limpo.copy()
    df_alu['Unidade Escolar'] = df_alu[col_ue_alu].astype(str).str.strip()
    df_alu['Turma'] = df_alu[col_cod_alu].astype(str).str.strip()
    antes_gb = df_alu.groupby(['Unidade Escolar', 'Turma']).size().reset_index(name='Total_Antes')
    
    col_ue_mat = 'Unidade Escolar' if 'Unidade Escolar' in df_matriculas_final.columns else df_matriculas_final.columns[0]
    col_cod_mat = 'Código da Turma Suap' if 'Código da Turma Suap' in df_matriculas_final.columns else df_matriculas_final.columns[1]
    df_mat = df_matriculas_final.copy()
    df_mat['Unidade Escolar'] = df_mat[col_ue_mat].astype(str).str.strip()
    df_mat['Turma'] = df_mat[col_cod_mat].astype(str).str.strip()
    depois_gb = df_mat.groupby(['Unidade Escolar', 'Turma']).size().reset_index(name='Total_Depois')
    
    comp_df = pd.merge(valid_turmas, antes_gb, on=['Unidade Escolar', 'Turma'], how='left')
    comp_df = pd.merge(comp_df, depois_gb, on=['Unidade Escolar', 'Turma'], how='left')
    
    comp_df['Total_Antes'] = comp_df['Total_Antes'].fillna(0).astype(int)
    comp_df['Total_Depois'] = comp_df['Total_Depois'].fillna(0).astype(int)
    comp_df['Diferenca'] = comp_df['Total_Antes'] - comp_df['Total_Depois']
    
    divergentes = comp_df[comp_df['Diferenca'] > 0].copy()
    divergentes = divergentes.sort_values(by=['Unidade Escolar', 'Turma'])
    
    if divergentes.empty:
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, "Nao houve divergencia de matriculas (nenhuma exclusao por duplicidade nas turmas do Eduten).", ln=1)
        return bytes(pdf.output())
    
    # Montar Cabeçalho da Tabela
    pdf.set_font("helvetica", 'B', 9)
    pdf.cell(90, 8, "Unidade Escolar", border=1)
    pdf.cell(40, 8, "Turma", border=1, align='C')
    pdf.cell(20, 8, "Inicial", border=1, align='C')
    pdf.cell(20, 8, "Final", border=1, align='C')
    pdf.cell(20, 8, "Excluidos", border=1, align='C')
    pdf.ln()
    
    pdf.set_font("helvetica", '', 8)
    for _, row in divergentes.iterrows():
        ue = str(row['Unidade Escolar'])
        if len(ue) > 42: ue = ue[:39] + "..."
        
        pdf.cell(90, 6, ue, border=1)
        pdf.cell(40, 6, str(row['Turma']), border=1, align='C')
        pdf.cell(20, 6, str(row['Total_Antes']), border=1, align='C')
        pdf.cell(20, 6, str(row['Total_Depois']), border=1, align='C')
        
        pdf.set_text_color(200, 0, 0)
        pdf.cell(20, 6, "-" + str(row['Diferenca']), border=1, align='C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln()

    # Detalhamento das Duplicadas
    pdf.ln(10)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "Matrículas Excluídas por Divergências ou Duplicidade", ln=1)
    pdf.cell(0, 6, "Esses dados foram encaminhados para a Diretoria de Supervisão Escolar para verificação.", ln=1)
    
    if df_dup_apos is None or df_dup_apos.empty:
        pdf.set_font("helvetica", '', 10)
        pdf.cell(0, 6, "Não há lista de alunos removidos por duplicidade.", ln=1)
    else:
        # Tabela Detalhamento
        pdf.set_font("helvetica", 'B', 8)
        cols = list(df_dup_apos.columns)
        col_nome = next((c for c in cols if 'NOME' in c), cols[0])
        col_mat = next((c for c in cols if 'MATR' in c or 'MATRIC' in c), None)
        col_cpf = 'CPF' if 'CPF' in cols else next((c for c in cols if 'DOCUMENTO' in c or 'CPF' in c), None)
        col_ue = next((c for c in cols if 'UNIDADE' in c or 'ESCOLA' in c or 'CAMPUS' in c), cols[2])
        col_tur = next((c for c in cols if 'TURMA' in c), cols[3])

        pdf.cell(55, 6, "Nome do Aluno", border=1)
        pdf.cell(20, 6, "Matrícula", border=1, align='C')
        pdf.cell(25, 6, "CPF", border=1, align='C')
        pdf.cell(65, 6, "Unidade Escolar", border=1)
        pdf.cell(30, 6, "Turma", border=1, align='C')
        pdf.ln()

        pdf.set_font("helvetica", '', 7)
        for _, row in df_dup_apos.iterrows():
            nome = str(row[col_nome])[:30] if pd.notnull(row[col_nome]) else ""
            mat = str(row[col_mat]).replace(".0", "").strip() if col_mat and pd.notnull(row[col_mat]) else "-"
            mat = mat[:15]
            cpf = str(row[col_cpf]) if col_cpf and pd.notnull(row[col_cpf]) else ""
            ue = str(row[col_ue])[:33] if pd.notnull(row[col_ue]) else ""
            turma_str = str(row[col_tur])[:15] if pd.notnull(row[col_tur]) else ""
            
            pdf.cell(55, 6, nome, border=1)
            pdf.cell(20, 6, mat, border=1, align='C')
            pdf.cell(25, 6, cpf, border=1, align='C')
            pdf.cell(65, 6, ue, border=1)
            pdf.cell(30, 6, turma_str, border=1, align='C')
            pdf.ln()

    return bytes(pdf.output())

def gerar_pdf_resumo_atualizacao(df_novas_matriculas, df_novos_professores):
    pdf = PDFResumo()
    pdf.add_page()
    pdf.set_font("helvetica", size=12)
    
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, "Resumo Analítico da Atualização", ln=1, align='C')
    pdf.set_font("helvetica", '', 11)
    pdf.multi_cell(0, 6, "Este relatório detalha os registros que não existiam na base 'Antes' e que foram inseridos como nova carga no sistema (cadastros novos de alunos ou professores).")
    pdf.ln(5)
    
    # MATRICULAS
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "1. Atualização de Matrículas", ln=1)
    
    if df_novas_matriculas is None or df_novas_matriculas.empty:
        pdf.set_font("helvetica", '', 10)
        pdf.cell(0, 6, "Nenhuma nova matrícula detectada na base 'Depois'.", ln=1)
    else:
        pdf.set_font("helvetica", '', 10)
        pdf.cell(0, 6, f"Total de Novas Matrículas: {len(df_novas_matriculas)}", ln=1)
        pdf.ln(2)
        
        # Agrupamento Quantitativo
        cols = list(df_novas_matriculas.columns)
        col_ue = next((c for c in cols if 'UNIDADE' in c.upper() or 'ESCOLA' in c.upper()), cols[0])
        col_tur = next((c for c in cols if 'TURMA' in c.upper()), cols[1] if len(cols)>1 else cols[0])
        
        df_agrupado = df_novas_matriculas.groupby([col_ue, col_tur]).size().reset_index(name='Qtd')
        df_agrupado = df_agrupado.sort_values(by=[col_ue, col_tur])
        
        pdf.set_font("helvetica", 'B', 9)
        pdf.cell(100, 7, "Unidade Escolar", border=1)
        pdf.cell(60, 7, "Turma", border=1, align='C')
        pdf.cell(30, 7, "Qtd Alunos", border=1, align='C')
        pdf.ln()
        
        pdf.set_font("helvetica", '', 8)
        for _, row in df_agrupado.iterrows():
            ue = str(row[col_ue])[:48] if pd.notnull(row[col_ue]) else ""
            tur = str(row[col_tur])[:22] if pd.notnull(row[col_tur]) else ""
            pdf.cell(100, 6, ue, border=1)
            pdf.cell(60, 6, tur, border=1, align='C')
            pdf.cell(30, 6, str(row['Qtd']), border=1, align='C')
            pdf.ln()
            
    pdf.ln(5)
    
    # PROFESSORES
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 8, "2. Atualização de Professores", ln=1)
    
    if df_novos_professores is None or df_novos_professores.empty:
        pdf.set_font("helvetica", '', 10)
        pdf.cell(0, 6, "Nenhum novo professor detectado na base 'Depois'.", ln=1)
    else:
        pdf.set_font("helvetica", '', 10)
        pdf.cell(0, 6, f"Total de Novos Vínculos: {len(df_novos_professores)}", ln=1)
        pdf.ln(2)
        
        cols_p = list(df_novos_professores.columns)
        col_ue_p = next((c for c in cols_p if 'UNIDADE' in c.upper() or 'ESCOLA' in c.upper()), cols_p[0])
        
        df_agrupado_p = df_novos_professores.groupby([col_ue_p]).size().reset_index(name='Qtd')
        df_agrupado_p = df_agrupado_p.sort_values(by=[col_ue_p])

        pdf.set_font("helvetica", 'B', 9)
        pdf.cell(160, 7, "Unidade Escolar", border=1)
        pdf.cell(30, 7, "Qtd Vínculos", border=1, align='C')
        pdf.ln()
        
        pdf.set_font("helvetica", '', 8)
        for _, row in df_agrupado_p.iterrows():
            ue = str(row[col_ue_p])[:78] if pd.notnull(row[col_ue_p]) else ""
            pdf.cell(160, 6, ue, border=1)
            pdf.cell(30, 6, str(row['Qtd']), border=1, align='C')
            pdf.ln()
            
    return bytes(pdf.output())
