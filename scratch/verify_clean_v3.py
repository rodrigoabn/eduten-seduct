import pandas as pd
import re

def clean_v3(x):
    if pd.isna(x) or str(x).lower() == 'nan' or str(x).strip() == '':
        return None
    try:
        # Handling scientific notation and floats
        val = float(x)
        s = '{:.0f}'.format(val)
    except:
        s = str(x)
    
    # Strip non-digits
    s = re.sub(r'\D', '', s)
    return s if s != '' else None

test_cases = [113838217.0, "113838217.0", "113.838.217-00", 2.024103e+13, "2.024103e+13", np.nan]
from numpy import nan
for t in test_cases:
    print(f"{t} -> {clean_v3(t)}")
