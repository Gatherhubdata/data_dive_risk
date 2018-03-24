
# coding: utf-8

# # Notebook to explore the Gather data sets provided
# 
# General information:
#  - there are multiple files containing preprocessed data

# In[1]:


pwd


# In[2]:


data_dir = '../data/wsup/tidy/'


# In[3]:


ls $data_dir


# In[4]:


import pandas_profiling
import pandas as pd


# ## Overview of the data files

# In[16]:


data_overview = pd.read_csv(data_dir + 'questionnaire_codebook.csv', index_col = 0)
data_overview


# ## Detailed data
# ### General background info on respondents and types of toilet
#  - note this is not aggregated by plot - what is the unique id?

# In[125]:


data1_orig = pd.read_csv(data_dir + 'tidy_data_questionnaire_section_2.csv')
pandas_profiling.ProfileReport(data1_orig)


# In[126]:


data1_orig.id.unique().shape, data1_orig.shape


# Find the unique index - is it id and respondent?
# It looks like type of toilet might also have a new row

# In[127]:


for key, grp in data1_orig.groupby(['id', 'respondent', 'type_of_toilet']):
    if grp.shape[0] > 1:
        print(grp[grp.columns.difference(['id', 'respondent'])].drop_duplicates().shape[0])


# We can see that within plot id and type of toilet that there can be multiple respondents but they always give the same responses

# In[128]:


for key, grp in data1_orig.groupby(['id','type_of_toilet']):
    if grp.shape[0] > 1:
        dups=grp[grp.columns.difference(['id','type_of_toilet', 'respondent', 'plot_months'])].drop_duplicates().shape[0]
        if dups > 1:
            print(grp)


# In[129]:


data1_orig.groupby(['id', 'respondent','type_of_toilet']).size().max()


# In[130]:


results = data1_orig.groupby('id')[['respondent', 'type_of_toilet']].agg(lambda x:len(set(x)))
results.columns= ['n_respondents', 'n_toilet_types']


# In[131]:


data1_orig = data1_orig.set_index('id').join(results)
data1_orig['n_respondents'].value_counts()


# In[133]:


data1_orig['n_toilet_types'].value_counts()


# In[137]:


data1 = data1_orig.reset_index()


# In[138]:


data1['respondent_ttype_id'] = data1.groupby('id')['respondent'].transform(lambda x:range(len(x)))


# In[139]:


data1['respondent_ttype_id'].value_counts()


# In[141]:


data1.groupby(['id', 'respondent_ttype_id']).size().max()


# In[142]:


data1.set_index(['id', 'respondent_ttype_id'], drop=False, inplace=True)


# In[143]:


data1.index.unique().shape, data1.shape


# ### More specific info on toilet use - unique by toilet user and plot ID?

# In[12]:


data3 = pd.read_csv(data_dir + 'tidy_data_questionnaire_section_3.csv')
pandas_profiling.ProfileReport(data3)


# It looks like waste disposal should be in data4, on the toilet type

# In[18]:


temp = data3[['id', 'solid_waste_disp']].drop_duplicates()
temp.shape


# In[22]:


data3.drop('solid_waste_disp', 1, inplace=True)


# Unique index check

# In[23]:


data3.set_index(['id', 'toilet_user'], inplace=True)


# In[26]:


data3.index.unique().shape, data3.shape


# ### Data on toilets that is aggregated by plot

# In[17]:


data4 = pd.read_csv(data_dir + 'tidy_data_questionnaire_section_4.csv')
pandas_profiling.ProfileReport(data4)


# Set the index

# In[19]:


data4 = data4.set_index('id')


# In[20]:


data4 = data4.join(temp.set_index('id'))


# In[28]:


data4.index.unique().shape, data4.shape


# In[21]:


data4.head()


# ### Toilets

# In[98]:


data5 = pd.read_csv(data_dir + 'tidy_data_questionnaire_section_5.csv')
pandas_profiling.ProfileReport(data5)


# # Questions

# ### (1) How consistent are responses across different people from the same plot

# In[38]:


data1.columns


# In[84]:


data1_dups = data1[data1.n_responders>1]


# In[94]:


for f in ['no_of_hhs',  'no_of_ppl', 'no_of_toilets']:
    temp = data1_dups.groupby('id')[f].apply(lambda x:list(x))
    temprange = temp.map(lambda x:max(x) - min(x))
    print(f, temprange.max())


# There is variance in the no of toilets

# In[97]:


data1[data1.id.isin(temprange[temprange==10].index)]


# Ah... the data set is also split based on type of toilet

# ### (2) What is the average number of toilets per plot

# In[ ]:


data1


# ### Average number of users per toilet

# In[ ]:




