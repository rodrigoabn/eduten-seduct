import pandas as pd
from etl_processor import obter_registros_novos

def test_diff():
    print("Testing Matriculas...")
    try:
        df_antes_mat = pd.read_excel('antes_matricula.xlsx')
        df_depois_mat = pd.read_excel('depois_matricula.xlsx')
        print(f"Base Antes (Matriculas): {len(df_antes_mat)} rows")
        print(f"Base Depois (Matriculas): {len(df_depois_mat)} rows")
        
        df_novos_mat = obter_registros_novos(df_antes_mat, df_depois_mat)
        print(f"New Matriculas found: {len(df_novos_mat)}")
        if not df_novos_mat.empty:
            print("Preview of new matriculas:")
            print(df_novos_mat.head())
    except Exception as e:
        print(f"Error testing matriculas: {e}")

    print("\nTesting Professores...")
    try:
        df_antes_prof = pd.read_excel('antes_professores.xlsx')
        df_depois_prof = pd.read_excel('depois_professores.xlsx')
        print(f"Base Antes (Professores): {len(df_antes_prof)} rows")
        print(f"Base Depois (Professores): {len(df_depois_prof)} rows")
        
        df_novos_prof = obter_registros_novos(df_antes_prof, df_depois_prof)
        print(f"New Professores found: {len(df_novos_prof)}")
        if not df_novos_prof.empty:
            print("Preview of new professores:")
            print(df_novos_prof.head())
    except Exception as e:
        print(f"Error testing professores: {e}")

if __name__ == "__main__":
    test_diff()
