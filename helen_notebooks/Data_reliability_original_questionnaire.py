
# coding: utf-8

# # Notebook to explore data reliability using the original questionnaire
# 
# The aims are:
#  - Uniquely identify rows so that multiple people can work on known data
#  - Identify unique plots
#  - look for inconsistencies that make the data unreliable
# 

# In[1]:


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno


# In[2]:


pd.options.display.max_rows = 300
pd.options.display.max_columns = 300
pd.options.display.max_colwidth = 300


# In[3]:


get_ipython().magic('matplotlib inline')


# ## Load the data

# In[4]:


data_orig = pd.read_excel('../data/wsup/raw/KANYAMA TOILET CENSUS QUESTIONNAIRE.XLSX', 
                          sheetname = 'KANYAMA TOILET CENSUS QUESTIONN', skiprows=1)


# ## Try to profile the data

# In[76]:


import pandas_profiling
pandas_profiling.ProfileReport(data_orig)


# We have a problem with some of the fields so we need to fix this first - it looks like Record plot number and 1.3 have dates in

# ## Quick missing value analysis

# In[5]:


msno.matrix(data_orig.sample(250))


# ## Drop unwanted columns

# In[6]:


drops = [line.strip() for line in open('../data/drops.txt')]
drops
data_orig.drop(drops, 1, inplace=True)


# In[7]:


data_orig.head(10)


# In[ ]:





# ## Uniquely identify each row
#  - we know there is no unique field already
#  - this ensures that others working with the data work on the same rows
#  - on loading the data pandas assigns a unique row id

# In[9]:


data_orig['Row_index'] = data_orig.index.map(lambda x: 'Row_%04d' % x)


# In[10]:


data_orig.set_index(['Row_index'], inplace=True)


# In[11]:


data_orig.shape


# ## Drop unwanted rows

# In[12]:


data = data_orig[(data_orig['IS THERE AN ELIGIBLE CANDIDATE TO INTERVIEW?\xa0'].str.contains('Yes')) & 
                (data_orig['Are you willing to participate?'].str.contains('Yes'))]
data.shape


# In[13]:


data.drop(['IS THERE AN ELIGIBLE CANDIDATE TO INTERVIEW?\xa0', 'Are you willing to participate?'], 1, inplace=True)


# ## Try again

# In[81]:


import pandas_profiling
pandas_profiling.ProfileReport(data[data.columns.difference(['1.3', 'Record plot number'])])


# In[14]:


data.dtypes


# Give up for now on profiling

# # Fix landlord, tenant, caretaker time

# In[16]:


import numpy as np


# In[17]:


data['sex'] = np.NaN
for c in ['Landlord ', 'Caretaker', 'Tenant']:
    x = 'DESCRIPTION OF RESPONDENT: %s - How long have you stayed/been associated with this plot? (magnitude)' % c
    y = 'DESCRIPTION OF RESPONDENT: %s - How long have you stayed/been associated with this plot? (units)' % c
    z = 'DESCRIPTION OF RESPONDENT: %s - SEX ' % c
    print(data[y].value_counts(dropna=False))
    # Units is often null - is it years or months? (assuming years)
    data['%s_time' % c.strip()] = data[[x,y]].apply(
        lambda row:row[x] if (y == 'Years') or (pd.isnull(y)) else row[x]/12, axis=1)
    data['sex'] = data[['sex',z]].apply(
        lambda row:row[z] if pd.notnull(row[z]) and pd.isnull(row['sex']) else row['sex'], axis=1)


# In[18]:


desc = [d for d in data.columns if d.startswith('DESCRIPTION OF')]
desc


# In[19]:


data.drop(desc, 1, inplace=True)


# ## Check responder-specific info now removed

# In[65]:


data.head()


# ### Record plot number is mentioned twice - are the same values given?

# In[20]:


data['Record plot number'].dtype


# In[26]:


data['Record plot number'].value_counts()


# In[37]:


remove = ["unknown", "0", "not known", "no number", "don't know", "un known"]
dicts = dict(zip(data['Record plot number'].unique(), 
                 ['ID_%04d' % r for r in range(data['Record plot number'].unique().shape[0])]))
data['New_plot_id'] = data['Record plot number'].map(
    lambda x: dicts[x] if (pd.notnull(x) & (str(x).strip().lower() not in remove)) else 'None')


# It looks like there are a lot of typos

# In[22]:


data.loc[data['Record plot number'] != data['1.3'], ['Record plot number', '1.3']].head(100)


# # What is a meaningful unit?
# Note that rows are responders

# In[38]:


data['New_plot_id'].unique().shape


# In[41]:


data['Responder_type'] = data[['Landlord_time', 'Caretaker_time', 'Tenant_time']].apply(
                            lambda x: 'Landlord' if pd.notnull(x[0]) 
                            else 'Caretaker' if pd.notnull(x[1]) 
                             else 'Tenant' if pd.notnull(x[2]) 
                            else 'Unknown', axis=1)
data['Responder_type'].value_counts(dropna=False)   


# ### Plot number and responder type?

# In[42]:


data.set_index(['New_plot_id', 'Responder_type']).index.unique().shape


# This means that responder and caretaker alone is not sufficient

# In[44]:


for key, grp in data.groupby(['New_plot_id', 'Responder_type']):
    if grp.shape[0] > 1:
        print(grp.shape, grp[grp.columns.difference(['New_plot_id', 'Responder_type'])].drop_duplicates().shape[0])


# Loads of plots with no ID and lack of responder info

# In[45]:


grp


# # EDA

# In[47]:


dtypes = data.dtypes
dtypes.value_counts()


# In[48]:


cat_cols = dtypes[dtypes == 'object' ].index
cat_cols


# In[49]:


cat_vars = ['RECORD TYPE OF PROPERTY', 'SELECT ZONE', 'SELECT ZONE (Other (please specify)) - specify', 
            'SELECT ZONE SECTION', '1.2', '1.3', '1.6.2', 'What is the designation of the respondent?', 
           'Where do you dispose your solid wastes?', 'How did you know about the service of emptying your toilet?', 
           'Was the fee you paid affordable?', 'CONTAINMENT/SUBSTRUCTURE']


# ## What is the distribution of these variables

# In[51]:


for c in cat_vars:
    
    if data[c].unique().shape[0] < 30:
        print(c)
        fig, ax = plt.subplots()
        sns.countplot(data.loc[data[c].notnull(), c], ax=ax)
        fig.autofmt_xdate()


# ## Dates of visits

# In[52]:


date_cols = dtypes[dtypes == 'datetime64[ns]' ].index


# In[53]:


fig, ax = plt.subplots()
data['DATE OF INTERVIEW'].value_counts().plot(ax=ax)


# ## Times of visits

# In[54]:


data['Time'] = data['DATE OF INTERVIEW (Time Answered)'].map(
    lambda x:x.replace(day=1, month=1) if pd.notnull(x) else pd.NaT)
temp = data[['Time', 'Record plot number']].set_index('Time').dropna()
temp.resample('10T').count().plot()


# In[55]:


data.head().T


# ## Explore landlord, tenant, caretaker time

# In[56]:


import numpy as np
sns.boxplot(x=data['RECORD TYPE OF PROPERTY'], y=data['Landlord_time'].map(lambda x:np.log(x+1)))


# In[57]:


sns.boxplot(x=data['RECORD TYPE OF PROPERTY'], y=data['Tenant_time'].map(lambda x:np.log(x+1)))


# In[58]:


sns.boxplot(x=data['RECORD TYPE OF PROPERTY'], y=data['Caretaker_time'].map(lambda x:np.log(x+1)))


# In[59]:


data[['Landlord_time', 'Caretaker_time', 'Tenant_time']].describe()


# Landlords have typically been there the longest... but note that some landlords have been there 164 years

# # Record type of property vs zone

# In[60]:


ct = pd.crosstab(data['SELECT ZONE'], data['RECORD TYPE OF PROPERTY'])
ct = ct.div(ct.sum(axis=0), axis=1)
sns.heatmap(ct, annot=True)


# In[61]:


data[data['RECORD TYPE OF PROPERTY']== 'Public Toilet ']


# ## Total number of toilets - lots of NaNs

# In[62]:


data['Total number of toilets{0}'].value_counts(dropna=False)


# In[76]:


temp = data[['Total_toilets_sum', 'Total number of toilets{0}']].max(axis=1)
temp.isnull().sum()


# In[77]:


toil_cols = ['1.6 - 1 - 1.5.1','1.6 - 2 - 1.5.1','1.6 - 3 - 1.5.1','1.6 - 4 - 1.5.1',
     '1.6 - 5 - 1.5.1','1.6 - 6 - 1.5.1','1.6 - 7 - 1.5.1','1.6 - 8 - 1.5.1']
data['Total_toilets_sum'] = data[toil_cols].sum(axis=1, min_count=1)
data['Total_toilets_sum'] =  data[['Total_toilets_sum', 'Total number of toilets{0}']].max(axis=1)


# In[66]:


data['Total_toilets_sum'].value_counts(dropna=False)


# In[67]:


data['Total_toilets_sum'].hist(bins=20)


# In[ ]:





# ## Do any residential plots not have any toilets?

# In[69]:


data[(data['RECORD TYPE OF PROPERTY']=='Residential Plot') & data['Total_toilets_sum'].isnull()].shape


# ## Strange patterns in categorical variables

# In[70]:


for c in cat_vars:
    if data[c].unique().shape[0] > 30: print(c,data[c].unique().shape[0]); continue
    fig, ax = plt.subplots(figsize=(10,8))
    sns.boxplot(x=data[c], y = data['Total_toilets_sum'], ax=ax)


# In[ ]:


## Household size by zone


# In[117]:


data.loc[data['1.4'].notnull(), '1.4'].astype(int).value_counts()


# # Residential only

# In[125]:


data_residential = data[data['RECORD TYPE OF PROPERTY'] == 'Residential Plot']


# In[126]:


data_residential.shape


# In[ ]:


## How often are there more than three toilets mentioned but not described?


# In[78]:


data.to_hdf('../data/wsup/tidy/data_tidied.h5', key='main')


# In[ ]:




