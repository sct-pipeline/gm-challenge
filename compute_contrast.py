#!/usr/bin/env python
# Compute contrast. Output values in stdout.
# Author: Julien Cohen-Adad

import pandas

# Read GM values
pd_gm = pandas.read_csv('signal_gm.csv')
# Convert to Series and filter out the 'None' values, which correspond to slices where there is no GM mask
pd_gm = pandas.to_numeric(pd_gm['BIN()'], errors='coerce', downcast='float')
ind = pd_gm.index[pd_gm > 0]

# Read WM values
pd_wm = pandas.read_csv('signal_wm.csv')
pd_wm = pandas.to_numeric(pd_wm['BIN()'], errors='coerce', downcast='float')

# Compute contrast
pd = abs(pd_gm[ind] - pd_wm[ind]) / pandas.DataFrame([pd_gm[ind], pd_wm[ind]]).min()
print(f'{pd.mean()}')
