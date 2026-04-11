import pandas as pd
import numpy as np

def limpar_id_v1(series):
    return series.astype(str).str.replace(r'\.0$', '', regex=True).str.strip().replace('nan', None)

def limpar_id_v2(series):
    def format_val(x):
        if pd.isnull(x) or str(x).lower() == 'nan' or str(x).strip() == '':
            return None
        try:
            # Se for float ou string que parece float, converte para int-like string
            f = float(x)
            return '{:.0f}'.format(f)
        except:
            return str(x).strip()
    return series.apply(format_val)

# Test cases
test_data = [2024103130101.0, "2024103130101", 123.0, "123.0", np.nan, "nan", "  456  "]
s = pd.Series(test_data)

print("Original:")
print(s)
print("\nV1 (Current):")
print(limpar_id_v1(s))
print("\nV2 (Proposed):")
print(limpar_id_v2(s))

# Verify equality of different formats
v2 = limpar_id_v2(s)
print("\nIs row 0 ('2024103130101.0') == row 1 ('2024103130101')?")
print(v2[0] == v2[1])
