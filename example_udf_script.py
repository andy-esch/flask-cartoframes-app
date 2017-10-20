import numpy as np; np.random.seed(); mean_val = df[col]; df['sim_col'] = np.random.poisson(mean_val, len(df))
