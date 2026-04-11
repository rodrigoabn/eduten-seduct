import pandas as pd
from etl_processor import obter_registros_novos

def investigate_df(name, df):
    print(f"\n--- Investigating {name} ---")
    print(f"Columns: {df.columns.tolist()}")
    col_cpf = next((c for c in df.columns if 'CPF' in c.upper() or 'DOCUMENTO' in c.upper()), None)
    col_mat = next((c for c in df.columns if 'MATR' in c.upper()), None)
    print(f"Detected CPF col: {col_cpf}")
    print(f"Detected MATR col: {col_mat}")
    
    if col_cpf:
        print(f"Sample CPF values: {df[col_cpf].head().tolist()}")
        print(f"Sample CPF dtypes: {df[col_cpf].dtype}")
    if col_mat:
        print(f"Sample Matrícula values: {df[col_mat].head().tolist()}")
        print(f"Sample Matrícula dtypes: {df[col_mat].dtype}")

def test_diff():
    print("Loading test files...")
    df_antes_mat = pd.read_excel('antes_matricula.xlsx')
    df_depois_mat = pd.read_excel('depois_matricula.xlsx')
    df_antes_prof = pd.read_excel('antes_professores.xlsx')
    df_depois_prof = pd.read_excel('depois_professores.xlsx')

    investigate_df("Antes Matricula", df_antes_mat)
    investigate_df("Depois Matricula", df_depois_mat)
    
    df_novos_mat = obter_registros_novos(df_antes_mat, df_depois_mat)
    print(f"\nNew Matriculas found: {len(df_novos_mat)}")
    
    investigate_df("Antes Professores", df_antes_prof)
    investigate_df("Depois Professores", df_depois_prof)
    
    df_novos_prof = obter_registros_novos(df_antes_prof, df_depois_prof)
    print(f"\nNew Professores found: {len(df_novos_prof)}")

if __name__ == "__main__":
    test_diff()
