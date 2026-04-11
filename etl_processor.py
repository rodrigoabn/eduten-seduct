import pandas as pd
import numpy as np
import io

def format_columns(df):
    df.columns = [str(col).strip() for col in df.columns]
    return df

def limpar_id(series):
    if series is None: return pd.Series(dtype=str)
    import re
    
    def _clean(x):
        if pd.isna(x) or str(x).lower() == 'nan' or str(x).strip() == '':
            return None
        try:
            # Tenta converter para float e formatar sem decimais para evitar notação científica
            val = float(x)
            s = '{:.0f}'.format(val)
        except:
            # Se tiver caracteres não numéricos (como traços no CPF), pega como string
            s = str(x)
        
        # Remove qualquer caractere que não seja número (pontos, traços, etc)
        s = re.sub(r'\D', '', s)
        return s if s != '' else None
            
    return series.apply(_clean)

def get_duplicates_cpf(df):
    df = format_columns(df)
    cols_upper = {col: col.upper() for col in df.columns}
    df_temp = df.rename(columns=cols_upper)
    if 'CPF' not in df_temp.columns:
        return pd.DataFrame()
    df_duplicados = df_temp[df_temp.duplicated(subset=['CPF'], keep=False)]
    if not df_duplicados.empty:
        df_duplicados = df_duplicados.sort_values(by='CPF')
    return df_duplicados

def etl_alunos(df_raw):
    df = format_columns(df_raw).copy()
    if 'Período Atual' in df.columns:
        df['Período Atual'] = df['Período Atual'].astype(str).str.replace(r'\.0', '', regex=True)
    if 'Turma Atual' in df.columns:
        df = df[df['Turma Atual'] != '-']
    if 'Descrição do Curso' in df.columns and 'Período Atual' in df.columns:
        condicao_anos_iniciais_1 = (df['Descrição do Curso'] == 'Ensino Fundamental Anos Iniciais') & (df['Período Atual'] == '1')
        df = df[~condicao_anos_iniciais_1]
    cursos_para_excluir = ['Educação Infantil','Educação de Jovens e Adultos Fases Iniciais','Educação de Jovens e Adultos Fases Finais','Educação de Jovens e Adultos Fases Finais (DIURNO)']
    if 'Descrição do Curso' in df.columns:
        df = df[~df['Descrição do Curso'].isin(cursos_para_excluir)]
    if 'Turma Atual' in df.columns:
        df = df[~df['Turma Atual'].astype(str).str.contains('.progressao.', case=False, regex=True, na=False)]
    
    if 'Descrição do Curso' in df.columns and 'Período Atual' in df.columns:
        condicoes = [
            (df['Descrição do Curso'] == 'Ensino Fundamental Anos Iniciais') & (df['Período Atual'] == '2'),
            (df['Descrição do Curso'] == 'Ensino Fundamental Anos Iniciais') & (df['Período Atual'] == '3'),
            (df['Descrição do Curso'] == 'Ensino Fundamental Anos Iniciais') & (df['Período Atual'] == '4'),
            (df['Descrição do Curso'] == 'Ensino Fundamental Anos Iniciais') & (df['Período Atual'] == '5'),
            (df['Descrição do Curso'] == 'Ensino Fundamental Anos Finais') & (df['Período Atual'] == '1'),
            (df['Descrição do Curso'] == 'Ensino Fundamental Anos Finais') & (df['Período Atual'] == '2'),
            (df['Descrição do Curso'] == 'Ensino Fundamental Anos Finais') & (df['Período Atual'] == '3'),
            (df['Descrição do Curso'] == 'Ensino Fundamental Anos Finais') & (df['Período Atual'] == '4')
        ]
        valores = ['2º Ano', '3º Ano', '4º Ano', '5º Ano', '6º Ano', '7º Ano', '8º Ano', '9º Ano']
        df['Ano de Escolaridade'] = np.select(condicoes, valores, default='Não Mapeado')
    
    if 'Turma Atual' in df.columns:
        split_turmas = df['Turma Atual'].astype(str).str.split('(', n=1, expand=True)
        df['Código da Turma Suap'] = split_turmas[0].str.strip()
        if len(split_turmas.columns) > 1:
            df['Sigla da turma Seduct'] = split_turmas[1].str.replace(')', '', regex=False).str.strip()
        else:
            df['Sigla da turma Seduct'] = None

    if 'Campus' in df.columns:
        df = df.rename(columns={'Campus': 'Unidade Escolar'})
    colunas_para_excluir = ['Descrição do Curso', 'Período Atual', 'Situação no Período', 'Turma Atual']
    df = df.drop(columns=[c for c in colunas_para_excluir if c in df.columns], errors='ignore')
    return df

def gerar_matriculas_eduten(df_alunos, df_escolas):
    df_alunos = format_columns(df_alunos).copy()
    df_escolas = format_columns(df_escolas).copy()
    if 'Nome SUAP' in df_escolas.columns and 'Unidade Escolar' in df_alunos.columns:
        lista_escolas_validas = df_escolas['Nome SUAP'].astype(str).str.strip().tolist()
        df_matriculas = df_alunos[df_alunos['Unidade Escolar'].astype(str).str.strip().isin(lista_escolas_validas)].copy()
        return df_matriculas
    return df_alunos

def remover_duplicidades(df_matriculas, df_duplicidades):
    if df_duplicidades.empty: return df_matriculas.copy()
    df_matriculas = format_columns(df_matriculas).copy()
    df_duplicidades = format_columns(df_duplicidades).copy()
    df_duplicidades.columns = df_duplicidades.columns.str.upper()
    col_cpf_mat = [col for col in df_matriculas.columns if str(col).strip().upper() == 'CPF']
    if 'CPF' not in df_duplicidades.columns or not col_cpf_mat:
        return df_matriculas
    nome_col_cpf = col_cpf_mat[0]
    df_duplicidades['CPF'] = df_duplicidades['CPF'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    df_matriculas[nome_col_cpf] = df_matriculas[nome_col_cpf].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    lista_cpfs_remover = df_duplicidades[df_duplicidades['CPF'] != 'nan']['CPF'].unique().tolist()
    df_matriculas_limpo = df_matriculas[~df_matriculas[nome_col_cpf].isin(lista_cpfs_remover)]
    return df_matriculas_limpo

def etl_turmas(df_turmas, df_escolas=None):
    df = format_columns(df_turmas).copy()
    if 'DESCRICAO' not in df.columns or 'CODIGO' not in df.columns:
        return df
    
    termos_exclusao = ['Educação de Jovens e Adultos Fases Finais', 'Educação de Jovens e Adultos Fases Iniciais', 'Educação Infantil']
    padrao_exclusao = '|'.join(termos_exclusao)
    df = df[~df['DESCRICAO'].astype(str).str.contains(padrao_exclusao, case=False, regex=True, na=False)]
    
    cond_anos_iniciais = df['DESCRICAO'].astype(str).str.contains('Ensino Fundamental Anos Iniciais', case=False, na=False)
    cond_1_periodo = df['DESCRICAO'].astype(str).str.contains('1º Período', case=False, na=False)
    df = df[~(cond_anos_iniciais & cond_1_periodo)]
    df = df[~df['CODIGO'].astype(str).str.contains('progress[aã]o', case=False, regex=True, na=False)]
    
    if 'CAMPUS' in df.columns:
        df = df.rename(columns={'CAMPUS': 'UNIDADES ESCOLARES'})
    df = df.drop(columns=['QTD DIARIOS', 'DIRETORIA', 'POLO'], errors='ignore')
    
    if df_escolas is not None:
        df_escolas = format_columns(df_escolas).copy()
        if 'Nome SUAP' in df_escolas.columns and 'UNIDADES ESCOLARES' in df.columns:
            lista_escolas_validas = df_escolas['Nome SUAP'].astype(str).str.strip().tolist()
            condicao_filtro = df['UNIDADES ESCOLARES'].astype(str).str.strip().isin(lista_escolas_validas)
            df = df[condicao_filtro].copy()
    
    colunas_ordenacao = ['UNIDADES ESCOLARES', 'DESCRICAO', 'SIGLA']
    colunas_presentes = [col for col in colunas_ordenacao if col in df.columns]
    if colunas_presentes:
        df = df.sort_values(by=colunas_presentes)
    return df

def etl_diarios(df_diarios, df_escolas=None):
    df = format_columns(df_diarios).copy()
    padrao_sigla = r'MATE\.|FUND\.'
    if 'Sigla do Componente' in df.columns:
        df = df[df['Sigla do Componente'].astype(str).str.contains(padrao_sigla, case=False, regex=True, na=False)]
    if 'Descrição do Componente' in df.columns:
        df = df[~df['Descrição do Componente'].astype(str).str.contains('1º Ano', case=False, na=False)]
    if 'Estrutura do Curso' in df.columns:
        cursos_permitidos = ['Ensino Fundamental Anos Finais', 'Ensino Fundamental Anos Iniciais']
        df = df[df['Estrutura do Curso'].isin(cursos_permitidos)]
    if 'Turma' in df.columns:
        df = df[~df['Turma'].astype(str).str.contains('progress[aã]o', case=False, regex=True, na=False)]
        df = df.drop_duplicates(subset=['Turma'], keep='first')
        
    if 'Descrição do Componente' in df.columns:
        mascara_sem_matematica = ~df['Descrição do Componente'].astype(str).str.contains('Matemática', case=False, na=False)
        df.loc[mascara_sem_matematica, 'Descrição do Componente'] = '-'
        mascara_com_matematica = df['Descrição do Componente'].astype(str).str.contains('Matemática', case=False, na=False)
        df.loc[mascara_com_matematica, 'Descrição do Componente'] = 'Matemática'
        
    if 'Professores' in df.columns:
        df['Professores'] = df['Professores'].astype(str).str.split(',')
        df = df.explode('Professores')
        df['Professores'] = df['Professores'].str.strip()
        df = df[(df['Professores'] != '') & (df['Professores'] != 'nan') & (df['Professores'] != 'None')]
        
    if 'Campus' in df.columns:
        df = df.rename(columns={'Campus': 'Unidade Escolar'})
    
    if 'Professores' in df.columns:
        split_prof = df['Professores'].astype(str).str.split(r'\(', n=1, expand=True)
        df['Professores'] = split_prof[0].str.strip()
        if len(split_prof.columns) > 1:
            df['Matrícula'] = split_prof[1].str.replace(r'\)', '', regex=True).str.strip()
        else:
            df['Matrícula'] = None
            
    if 'Turma' in df.columns:
        split_turma = df['Turma'].astype(str).str.split(r'\(', n=1, expand=True)
        df['Turma'] = split_turma[0].str.strip()
        if len(split_turma.columns) > 1:
            df['Sigla da Turma'] = split_turma[1].str.replace(r'\)', '', regex=True).str.strip()
        else:
            df['Sigla da Turma'] = None
            
    if df_escolas is not None:
        df_escolas = format_columns(df_escolas).copy()
        if 'Nome SUAP' in df_escolas.columns and 'Unidade Escolar' in df.columns:
            lista_escolas_validas = df_escolas['Nome SUAP'].astype(str).str.strip().tolist()
            condicao_filtro = df['Unidade Escolar'].astype(str).str.strip().isin(lista_escolas_validas)
            df = df[condicao_filtro].copy()
            
    if 'Professores' in df.columns:
        df = df.sort_values(by='Professores', ascending=True)
    df['#'] = range(1, len(df) + 1)
    
    colunas_ordem_final = ['#', 'Matrícula', 'Professores', 'Descrição do Componente', 'Unidade Escolar', 'Turma', 'Sigla da Turma', 'Estrutura do Curso']
    colunas_presentes = [col for col in colunas_ordem_final if col in df.columns]
    return df[colunas_presentes]

def cruzar_diarios_servidores(df_diarios, df_servidores=None, df_edu=None):
    df_final = df_diarios.copy()
    if 'Matrícula' not in df_final.columns:
        return df_final
    df_final['Matrícula'] = df_final['Matrícula'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    if df_servidores is not None:
        df_serv = format_columns(df_servidores).copy()
        df_serv.columns = df_serv.columns.str.upper()
        if 'MAT.' in df_serv.columns:
            df_serv['MAT.'] = df_serv['MAT.'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            colunas_desejadas = ['MAT.', 'CPF', 'TELEFONE', 'EMAIL']
            colunas_presentes = [col for col in colunas_desejadas if col in df_serv.columns]
            df_serv_reduzido = df_serv[colunas_presentes].drop_duplicates(subset=['MAT.'], keep='first')
            df_final = pd.merge(df_final, df_serv_reduzido, left_on='Matrícula', right_on='MAT.', how='left')
            if 'MAT.' in df_final.columns:
                df_final = df_final.drop(columns=['MAT.'])
                
    if df_edu is not None:
        df_edu = format_columns(df_edu).copy()
        if 'Employee ID' in df_edu.columns:
            df_edu['Employee ID'] = df_edu['Employee ID'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            mapa_colunas_edu = {
                'Employee ID': 'Employee ID',
                'Email Address [Required]': 'EMAIL_INSTITUCIONAL',
                'Work Phone': 'Telefone 2',
                'Home Phone': 'Telefone 3',
                'Mobile Phone': 'Telefone 4'
            }
            colunas_edu_presentes = [col for col in mapa_colunas_edu.keys() if col in df_edu.columns]
            df_edu_reduzido = df_edu[colunas_edu_presentes].drop_duplicates(subset=['Employee ID'], keep='first')
            renomeios = {k: v for k, v in mapa_colunas_edu.items() if k in colunas_edu_presentes and k != 'Employee ID'}
            df_edu_reduzido = df_edu_reduzido.rename(columns=renomeios)
            df_final = pd.merge(df_final, df_edu_reduzido, left_on='Matrícula', right_on='Employee ID', how='left')
            if 'Employee ID' in df_final.columns:
                df_final = df_final.drop(columns=['Employee ID'])
                
    return df_final
    
def df_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def obter_registros_novos(df_antes, df_depois):
    if df_antes is None or df_antes.empty:
        return df_depois if df_depois is not None else pd.DataFrame()
    if df_depois is None or df_depois.empty:
        return pd.DataFrame()
        
    df_antes = format_columns(df_antes)
    df_depois = format_columns(df_depois)
    
    # helper internal to apply cleaning and check validity
    def get_valid_keys(df, keywords):
        col = next((c for c in df.columns if any(k in c.upper() for k in keywords)), None)
        if col:
            keys = limpar_id(df[col]).dropna()
            if not keys.empty:
                return col, keys.unique().tolist()
        return None, []

    # 1. Try CPF/DOCUMENTO
    col_antes, antes_keys = get_valid_keys(df_antes, ['CPF', 'DOCUMENTO'])
    col_depois = next((c for c in df_depois.columns if any(k in c.upper() for k in ['CPF', 'DOCUMENTO'])), None)
    
    if col_antes and col_depois and antes_keys:
        df_depois_temp = df_depois.copy()
        df_depois_temp['ID_LIMPO'] = limpar_id(df_depois_temp[col_depois])
        df_novos = df_depois_temp[~df_depois_temp['ID_LIMPO'].isin(antes_keys)].drop(columns=['ID_LIMPO'])
        return df_novos
        
    # 2. Try MATRICULA
    col_antes, antes_keys = get_valid_keys(df_antes, ['MATR'])
    col_depois = next((c for c in df_depois.columns if any(k in c.upper() for k in ['MATR'])), None)
    
    if col_antes and col_depois and antes_keys:
        df_depois_temp = df_depois.copy()
        df_depois_temp['ID_LIMPO'] = limpar_id(df_depois_temp[col_depois])
        df_novos = df_depois_temp[~df_depois_temp['ID_LIMPO'].isin(antes_keys)].drop(columns=['ID_LIMPO'])
        return df_novos
        
    # 3. Fallback to full row exact match
    common_cols = list(set(df_antes.columns).intersection(set(df_depois.columns)))
    if not common_cols:
        return df_depois
        
    df_diff = pd.merge(df_depois, df_antes[common_cols], indicator=True, how='outer').query('_merge=="left_only"').drop('_merge', axis=1)
    return df_diff
