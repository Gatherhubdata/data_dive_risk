
# coding: utf-8

# # Notebook to generate a dataframe that captures data reliability

# Perform a series of tests/questions on each row and score the result based on 0 (missing), 1 (ambiguous), 2 (present)
# - is the plot number recorded? If not, this makes it very difficult to identify the plot as unique vs others (2 if different from 1.2)
# - is the type of property recorded? Very difficult to interpret the results if we don’t know this
# - does the plot have a zone? (Other means ambiguous)
# - does the plot have a zone section?
# - does the plot have toilets (sum should not include disused)
# - does the plot receive water?
# - who is the respondent (2 for landlord, 1 for caretaker and tenant, 0 for unknown)
# - was gps info captured?)
# - does the number of users sum up to the initial value
# - do they know where they dispose of solid wastes?
# - do they know if the toilet has been upgraded- no not reliable if they haven’t been there 2 years
# - Do they know they age of toilet?
# - Do they give age of toilet if more than 1
# - Do they know if the toilet has been emptied?
# - Do they know how much they spent?
# - Do they know how often they empty it?
# - Do they give a value for emptying it but have never actually emptied it
# - Is the toilet accessible but has never been emptied?
# - Is property recorded as not residential but a tenant answering questions
# - Toilet is not feasible for emptying but they have
# 
# ## List of possible inconsistencies that people have mentioned (excluding geospatial which are being dealt with separately
#  - visit information
#       - length of time of responder on plot - if units is not a number
#       - weird time of visit
#  - plot types
#      - no Record plot number
#      - record plot numbers are not equal
#      - zone and gps don't correspond
#      - number of families on the plot
#      - number of people on plot
#      - people living on the plot vs toilet users
#  - toilet types
#     - no toilets

# In[2]:


import pandas as pd


# In[7]:


pd.options.display.max_rows = 300
pd.options.display.max_columns = 300
pd.options.display.max_colwidth = 300


# In[289]:


data_orig = pd.read_hdf('../data/wsup/tidy/data_tidied.h5', key='main')


# In[290]:


name_changes = dict([line.strip().split('\t') for line in open('../data/name_changes.txt')])


# In[291]:


data = data_orig.rename(columns=name_changes)


# In[292]:


drops = [line.strip() for line in open('../data/drop2.txt')]
drops = data.columns.intersection(drops)
data.drop(drops, 1, inplace=True)


# In[293]:


data.shape


# In[294]:


drops = [d for d in data.columns if not (d.startswith('bool') or d.startswith('cat') or d.startswith('str') or
                                         d.startswith('num') or d.startswith('id') or d.startswith('date'))]
drops
data.drop(drops, 1, inplace=True)


# In[295]:


data.head(10).T


# In[85]:


results = pd.DataFrame(index = data.index)


# ## Plot id

# In[347]:


data[['id_new_plot_id', 'id_plot', 'str_plot_id', 'bool_plot_id']].head()


# In[87]:


results['Plot_id'] = data[['id_new_plot_id', 'id_plot', 'str_plot_id']].apply(
    lambda x: 2 if  x[0] != 'None' and x[1]==x[2] else 1 if (x[0]!= 'None') else 0, axis=1)


# In[88]:


results['Plot_id'].value_counts()


# In[346]:


data.loc[results.Plot_id == 2, ['id_new_plot_id', 'id_plot', 'str_plot_id']].head()


# ## Property type

# In[91]:


p = 'Property_type'
cols = ['cat_property','cat_property_other']


# In[96]:


results[p] = data[cols].apply(
    lambda x: 2 if not ('Other' in str(x[0])) or pd.isnull(x[0]) else 1 if pd.notnull(x[1]) else 0, axis=1)


# In[97]:


results[p].value_counts()


# In[100]:


data.loc[results[p] == 2, cols]


# In[102]:


data.loc[results[p] == 2, cols[0]].value_counts()


# ## Property zone

# In[104]:


p = 'Property_zone'
cols = [ 'cat_zone', 'cat_zone_other', 'cat_zone_section',
       'cat_zone_section_other', 'str_zone_name']


# In[105]:


data[cols]


# In[109]:


results[p] = data[cols].apply(
    lambda x: 2 if not ('Other' in str(x[0])) or pd.isnull(x[0]) else 1 if x.notnull().sum()>1 else 0, axis=1)


# In[110]:


results[p].value_counts()


# In[111]:


data.loc[results[p] == 0, cols]


# In[112]:


data.loc[results[p] == 2, cols[0]].value_counts()


# In[ ]:





# ## Toilets
#  - only relevant for residential
#  - suspicious if more than 1 toilet per person or no toilets
#  - 0 if info unknown

# In[296]:


data['num_toilets_per_person'] = data['num_toilets_all'] / data['num_ppl'].map(lambda x: np.NaN if x==0 else x)


# In[297]:


p = 'Toilets_total'
cols = [ 'num_toilets_all', 'num_toilets_per_person', 'cat_property']


# In[298]:


data.loc[data['num_toilets_per_person'].notnull(), 'num_toilets_per_person'].hist(bins=50)


# In[299]:


data[cols]


# In[300]:


results[p] = data[cols].apply(
    lambda x: np.NaN if x[2] != 'Residential Plot' else 
    2 if x[0]>0 and x[1]>0 and x[1] <=1 else 
    1 if (x[0]==0) or (x[1]>1) else 
    0, axis=1)


# In[301]:


results[p].value_counts()


# In[302]:


data.loc[results[p] == 0, cols]


# In[303]:


data.loc[results[p] == 2, cols[0]].value_counts()


# In[ ]:





# ## Water

# In[119]:


p = 'Water_collection'
cols = [ 'cat_water', 'cat_water_other']


# In[128]:


data[cols]


# In[130]:


results[p] = data[cols].apply(
    lambda x: 2 if 'Other' not in str(x[0]) and pd.notnull(x[0]) else 1 if pd.notnull(x[1]) else 0, axis=1)


# In[131]:


results[p].value_counts()


# In[132]:


data.loc[results[p] == 0, cols]


# In[133]:


data.loc[results[p] == 2, cols[0]].value_counts()


# ## Respondent

# In[146]:


p = 'Respondent_type'
cols = [ 'cat_responder_type']


# In[147]:


data[cols]


# In[152]:


results[p] = data[cols].apply(
    lambda x: 2 if x[0]=='Landlord' else 1 if x[0] in ['Caretaker', 'Tenant'] else 0, axis=1)


# In[153]:


results[p].value_counts()


# In[154]:


data.loc[results[p] == 0, cols]


# In[155]:


data.loc[results[p] == 2, cols[0]].value_counts()


# # GPS information

# In[159]:


data.columns


# In[161]:


p = 'GPS_presence'
cols = ['str_gps_lat']


# In[162]:


data[cols]


# In[163]:


results[p] = data[cols].apply(
    lambda x: 2 if pd.notnull(x[0]) else 0, axis=1)


# In[164]:


results[p].value_counts()


# In[165]:


data.loc[results[p] == 0, cols]


# In[166]:


data.loc[results[p] == 2, cols[0]].value_counts()


# # Number of users and num of ppl

# In[168]:


p = 'People_numbers_consistency'
cols = ['num_ppl', 'num_c_m', 'num_c_f', 'num_a_m',
       'num_a_f']


# In[169]:


data[cols]


# In[170]:


results[p] = data[cols].apply(
    lambda x: 2 if x[1:].sum()==x[0] else 1 if abs(x[1:].sum()-x[0]) < 2 else 0, axis=1)


# In[171]:


results[p].value_counts()


# In[172]:


data.loc[results[p] == 0, cols]


# In[173]:


data.loc[results[p] == 2, cols[0]].value_counts()


# ## People household - not relevant if not residential

# In[304]:


import numpy as np


# In[305]:


data['ppl_per_household'] = data['num_ppl'] / data['num_hhs']


# In[306]:


p = 'People_household'
cols = ['num_ppl', 'num_hhs', 'cat_property', 'ppl_per_household']


# In[307]:


ax = data['ppl_per_household'].hist(bins=100)
ax.set_yscale('log')
ax.set_xscale('log')


# In[308]:


data.loc[(data.cat_property == 'Residential Plot') & (data.ppl_per_household > 20),cols]


# In[309]:


results[p] = data[cols].apply(
    lambda x: np.NaN if x[2] != 'Residential Plot' else 
    2 if x[0] > x[1] and x[3] <=20 else 1 if x.isnull().sum()==0 else 0, axis=1)


# In[310]:


data.columns


# In[311]:


data.loc[results[p] == 2, cols]


# In[312]:


results[p].value_counts()


# In[180]:


data.loc[results[p] == 2, cols]


# ## Solid wastes

# In[244]:


p = 'Solid waste'
cols = [ 'cat_waste', 'cat_waste_other']


# In[245]:


data[cols].head()


# In[246]:


results[p] = data[cols].apply(
    lambda x: 2 if 'Other' not in str(x[0]) and pd.notnull(x[0]) else 1 if pd.notnull(x[1]) else 0, axis=1)


# In[247]:


results[p].value_counts()


# In[250]:


data.loc[results[p] == 0, cols]


# In[173]:


data.loc[results[p] == 2, cols[0]].value_counts()


# # Responder time vs age of toilet

# In[313]:


data['num_time_responder']  = np.NaN
for z in ['num_landlord_time','num_caretaker_time', 'num_tenant_time']:
    data['num_time_responder'] = data[['num_time_responder', z]].apply(
        lambda row:row[z] if pd.notnull(row[z]) and pd.isnull(row['num_time_responder']) else row['num_time_responder'], axis=1)


# In[314]:


for t in ['1','2', '3']:
    data['num_toilet%s_age' % t] = data['num_toilet%s_age_m' % t].map(
        lambda x:0 if pd.isnull(x) else x+1e-15) +  data['num_toilet%s_age_y' % t].map(
        lambda x:0 if pd.isnull(x) else x+1e-15)*12
    data['num_toilet%s_age' % t] = data['num_toilet%s_age' % t]/12


# In[315]:


data[['num_toilet%s_age_y' % t for t in ['1','2', '3']]].head()


# In[316]:


p = 'Age_of_toilet_reliability'
cols = ['num_time_responder'] + ['num_toilet%s_age' % t for t in ['1','2', '3']]


# In[317]:


data[cols].head()


# In[318]:


results[p] = data[cols].apply(
    lambda x: 2 if x[0]>x[1:].max() else 1 if x[1:].sum()>0 else 0, axis=1)


# In[319]:


results[p].value_counts()


# In[320]:


data.loc[results[p] == 0, cols]


# In[276]:


data.loc[results[p] == 2, cols[0]].value_counts()


# # Toilet details vs number of toilets

#  - not compete

# In[321]:


p = 'Toilet_details'
cols = [ 'num_toilets_all', 'bool_upgrade_2y',
       'bool_upgrade_2y_dn', 'cat_toilet_upgrade_type_3m','cat_toilet_full',
       'cat_toilet_full_other', 'bool_toilet_emptied', 'cat_toilet_emptied',
       'cat_toilet_emptied_who', 'cat_toilet_emptied_price',
       'cat_toilet_emptied_freq', 'cat_cleanliness', 'cat_roof_other',
       'cat_walls', 'cat_walls_other', 'cat_slab', 'cat_slab_other',
       'cat_interface', 'cat_interact_other', 'cat_containment',
       'cat_containment_other', 'cat_condition_roof', 'cat_condition_wall',
       'cat_condition_floor', 'cat_condition_interface',
       'cat_condition_containmenet', 'bool_sludge', 'cat_emptying_feasible',
       'cat_emptying_feasible_dn', 'cat_handwashing', 'cat_overflow',
       'bool_vacuum', 'bool_light', 'bool_pushcart', 'bool_disability',
       'bool_children', 'bool_wan']


# In[322]:


data.loc[data.num_toilets_all.isin([np.NaN, 0]), cols].head()


# In[325]:


data.loc[data.num_toilets_all.isin([np.NaN, 0]), cols].notnull().sum(axis=1).hist()


# In[339]:


results[p] = data[cols].apply(
    lambda x: 2 if (x[0] not in [np.NaN, 0]) and (x[1:].notnull().sum() > 20) else 
    1 if (x[0] in [np.NaN, 0]) and (x[1:].notnull().sum() > 30) or (x[0] not in [np.NaN, 0])
    else 0, axis=1)


# In[340]:


results[p].value_counts()


# In[336]:


data.num_toilets_all.isnull().sum()


# In[332]:


data.loc[results[p] == 0, cols]


# In[173]:


data.loc[results[p] == 2, cols[0]].value_counts()


# Not yet finished
#  - do they know if the toilet has been upgraded- no not reliable if they haven’t been there 2 years
# - Do they know they age of toilet?
# - Do they give age of toilet if more than 1
# - Do they know if the toilet has been emptied?
# - Do they know how much they spent?
# - Do they know how often they empty it?
# - Do they give a value for emptying it but have never actually emptied it
# - Is the toilet accessible but has never been emptied?
# - Is property recorded as not residential but a tenant answering questions
# - Toilet is not feasible for emptying but they have
#  - is the row very similar to any other

# In[241]:


data.columns


# In[348]:


results.to_hdf('../data/wsup/tidy/data_tidied.h5', key='resuts')


# # Summary results

# ### Proportion of fields with glowing results

# In[341]:


results[results.mean(axis=1)==2].shape[0] / results.shape[0]


# ### Spread of average scores

# In[342]:


get_ipython().magic('matplotlib inline')
import seaborn as sns
sns.set(font_scale=1.4)


# In[343]:


g = results.mean(axis=1).hist(figsize=(10,8))
g.set_xlabel('Average_score')
g.set_ylabel('Number of rows')


# # Scores by field

# In[344]:


g = results.mean(axis=0).hist(figsize=(10,8))
g.set_xlabel('Average_score')
g.set_ylabel('Number of fields')


# In[345]:


results.mean(axis=0).sort_values(ascending=False)


# In[ ]:




