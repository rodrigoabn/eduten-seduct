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
