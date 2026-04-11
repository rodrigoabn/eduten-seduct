import pandas as pd
from etl_processor import remover_professores_blacklist, limpar_id

def test_blacklist():
    # Mock some professor data
    df_prof = pd.DataFrame({
        'Matrícula': [1, 2, 4, 10, 20],
        'Nome': ['João', 'Castelo', 'Prisco', 'Permanecer', 'Ficar'],
        'Unidade Escolar': ['UE1', 'UE2', 'UE3', 'UE4', 'UE5']
    })
    
    # Load complementador
    df_comp = pd.read_excel('complementador.xls')
    print("Blacklist IDs found in complementador.xls:")
    col_mat = next((c for c in df_comp.columns if 'MATR' in c.upper()), None)
    print(limpar_id(df_comp[col_mat]).tolist())
    
    # Apply filter
    df_filtered = remover_professores_blacklist(df_prof, df_comp)
    
    print("\nProfessors before filtering:", len(df_prof))
    print(df_prof['Matrícula'].tolist())
    
    print("\nProfessors after filtering:", len(df_filtered))
    print(df_filtered['Matrícula'].tolist())
    
    # Check if 1, 2, 4 are gone (as seen in my previous head of complementador)
    for m in [1, 2, 4]:
        if m in df_filtered['Matrícula'].tolist():
            print(f"FAILED: ID {m} still present!")
        else:
            print(f"SUCCESS: ID {m} removed.")

if __name__ == "__main__":
    test_blacklist()
