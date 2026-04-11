import pandas as pd
from etl_processor import limpar_id

def check_intersection():
    df_antes = pd.read_excel('antes_matricula.xlsx')
    df_depois = pd.read_excel('depois_matricula.xlsx')
    
    col_mat_antes = next((c for c in df_antes.columns if 'MATR' in c.upper()), None)
    col_mat_depois = next((c for c in df_depois.columns if 'MATR' in c.upper()), None)
    
    if col_mat_antes and col_mat_depois:
        antes_mats = set(limpar_id(df_antes[col_mat_antes]).dropna().tolist())
        depois_mats = set(limpar_id(df_depois[col_mat_depois]).dropna().tolist())
        
        intersection = antes_mats.intersection(depois_mats)
        print(f"Unique Mats in Antes: {len(antes_mats)}")
        print(f"Unique Mats in Depois: {len(depois_mats)}")
        print(f"Intersection size: {len(intersection)}")
        
        if len(intersection) > 0:
            print(f"Sample intersection: {list(intersection)[:5]}")
        else:
            print("NO INTERSECTION FOUND.")
            print(f"Sample Antes: {list(antes_mats)[:5]}")
            print(f"Sample Depois: {list(depois_mats)[:5]}")

if __name__ == "__main__":
    check_intersection()
