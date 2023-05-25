import pandas as pd
import numpy as np
import os

# map multiple source column names and values with destination ones
def map_multiple_cols(data, mp, source_name):
	mp = mp[mp["source_name"] == source_name]
	map_col_list = list(mp.loc[mp["source_var_name"].isin(data.columns), "source_var_name"])
	map_col_list = np.unique(map_col_list)
	
	if len(map_col_list)!= 0:
		for name in map_col_list:
			df_mapper = mp.loc[mp['source_var_name'] == name]
			dic_value_mapper = pd.Series(df_mapper['destination_var_value'].values, index=df_mapper['source_var_value'].values).to_dict()
			data[name].replace(dic_value_mapper, inplace = True)

	df_mapper = mp.loc[mp['source_name'] == source_name]
	dic_name_mapper = pd.Series(df_mapper['destination_var_name'].values, index=df_mapper['source_var_name'].values).to_dict()
	data.rename(dic_name_mapper, axis=1, inplace=True)

	return data

# map single column in source table
def map_single_col(source_table, source_col, map_table, map_col):
	cols = [source_col] + [map_col]
	dic = map_table[cols].set_index(source_col).to_dict()
	source_table[source_col] = source_table[source_col].map(dic[map_col])

	return source_table

# calculate the difference of two dates
def calculate_date(df, col_start, col_end, digit=1):
    diff = ((df[col_start] - df[col_end]) / np.timedelta64(1, 'Y')).round(digit)

    for index, value in enumerate(diff):
        if value and value < 0:
            diff[index] = None

    return diff

def calculate_age(df, col_old, col_new):
    df[col_new] = np.nan
    df[col_new] = (df[col_old]/365).round(1)
    
    return df

# add a checker for cols and add missing columns
def check_add_cols(df, dic):
    cols = dic['system_variable_name']

    if cols.isin(df.columns).all():
        print('The columns are checked and matched with dictionary.')
    else:
        add_col = [] # find missing columns
        for col in cols:
            if not col in df.columns:
                add_col.append(col)
        #add missing columns
        for col in add_col:
            df[col] =  np.nan
            print('Add column: ' + col)

    #reorder columns
    df = df[cols]
    
    return df

# create system_patient_id col
def create_id_col(df, new_id_col, map_id_col, new_col_prefix, size_num):

    #if the id column has some ids, add ids to empty rows
    if not df[new_id_col].isnull().all():
        df = df.sort_values(new_id_col)
        last_row_id = df.loc[~df[new_id_col].isnull(),new_id_col][-1:].values[0] # select last patient id that has a value
        last_row_id = pd.to_numeric(last_row_id.lstrip(new_col_prefix)) # find the numeric id number of the last nonempty patient id
        new_col_empty = df.loc[df[new_id_col].isnull(),[map_id_col, new_id_col]].reset_index() ##filter out the empty new_col and add new id based on a sequence starting from the number of last patient id
        new_col_empty[new_id_col] = last_row_id + new_col_empty.groupby(map_id_col, sort=False).ngroup() + 1 # add new id sequence
        new_col_empty[new_id_col] = new_col_empty[new_id_col].astype(str).apply(lambda x: new_col_prefix + x.zfill(size_num)) #create new id
        new_col_empty_dic = new_col_empty.set_index(map_id_col)[new_id_col].to_dict()
        df[new_id_col] = df[new_id_col].fillna(df[map_id_col].map(new_col_empty_dic))
    else: #if the id column has no ids, create new ids
        # df[new_id_col] = np.nan
        df[new_id_col] = df.index + 1
        # df[new_id_col] = df.groupby(map_id_col, sort=False).ngroup() + 1 #add new id sequence
        df[new_id_col] = df[new_id_col].astype(str).apply(lambda x: new_col_prefix + x.zfill(size_num)) #create new id sequence

    return df

# when one patient has duplicated record, make utsw_pcdc_id unique for one record
def add_record_id(df, record_id_col, record_suffix):
    #count duplicated records
    df['duplicate_count'] = df.groupby(record_id_col, as_index=False)[record_id_col].cumcount()
    #add suffix to duplicated record ID
    df[record_id_col] = df.apply(lambda x: (x[record_id_col] + record_suffix + str(x['duplicate_count']+1)) if x['duplicate_count']> 0 else x[record_id_col], axis=1)
    df = df.drop('duplicate_count', axis=1)

    return df

def dic_cb_checker(df, dic_cb):
    """
    this checker is to check if the value in the output column is not included
    in the corresponding value in the dictionary_codebook file
    """
    df_cols = pd.Series(df.columns.tolist())
    cb_cols = df_cols.loc[df_cols.isin(np.unique(dic_cb.system_variable_name)),]

    msg = ''
    for col_name in cb_cols:
        df_values = df[col_name].value_counts()
        dic_cb_values = dic_cb[dic_cb['system_variable_name']==col_name].value.unique()
        
        for val, amount in df_values.items():
            if val not in dic_cb_values:
                msg += '[ATTN] Some variable in the output table is not matched in the dictionary_codebook: [\'{}\'] mismatch in the [\'{}\'] column. \n'.format(val, col_name) 

    if len(msg) ==0:
        msg += 'Success, all variables in output table are contained in dictionary_codebook'  

    return msg        


def null_val_checker(df, dic):
    """
    this checker is to check if there is null value in not nullable columns according to dictionary file
    """
    not_null_cols = dic.loc[dic['nullable']=='No', 'system_variable_name']
    df_cols = pd.Series(df.columns.tolist())
    df_cols = df_cols.loc[df_cols.isin(np.unique(not_null_cols))].values.tolist()

    msg = ''
    for var in df_cols:
        tmp_df = df.loc[pd.isna(df[var]), var]
        tmp_msg = ''
        for index, content in tmp_df.items():
            tmp_msg = 'Some null values found in the column [\'{}\'].\n'.format(var)
        
        msg += tmp_msg

    if not msg:
        msg += 'Success, no null value found in not nullable columns.'    

    return msg

def checker_dictionary(output_table,table_source, dic):
    """ check if columns and variables from the script output are all included in the information model.
    If not, pick out those not appear in the IM file.
    output_table: i.e., pe_patient
    table_source: the  `table_name` column subset. i.e., 'pe_patient','cr_patient'
    dic: import from the IM/dictionary.csv
    """
    source_var = output_table.columns.to_series()
    dic_var = dic[dic['table_name'] == table_source].system_variable_name
    mismatch = pick_notin(source_var,dic_var)
    # mismatch = mismatch[~pd.isnull(mismatch)] # allows NaN in data
    msg = ''
    if mismatch.shape[0] > 0:
        msg +='[ATTN] Some source variable were NOT MATCHED to IM_dictionary: {}'.format(mismatch)
    else: 
        msg += 'Success, all columns in output table are MATCHED with dictionary'
    return msg
    # if msg:
    #     raise ValueError(msg)

def pick_notin(a, b):
    '''Pick the element that in the a but not in the b'''
    # a: pandas.core.series.Series
    # b: pandas.core.series.Series
    c = np.empty(0)
    for element in a.unique():
        if element not in b.unique(): c = np.append(c,element)
    return c

def one_to_many_id(data, col1, col2):
    """ col1: the one ID column
    col2: is the many ID column that may related to one ID in col1
    this is to check if one ID in col2 is matched with multiple ID in col1
    """
    tmp = data[data[[col1,col2]].duplicated()== False]
    output = tmp[tmp[col2].duplicated(keep=False)]
    msg = ''
    if output.shape[0] >0:
        msg += '[ATTN] The one-to-many relationship between {} and {} is violates'.format(col1, col2)
    else:
        msg +='Success >>> The one-to-many relationship between{} and {}is verified'.format(col1, col2)
    return msg

## age checker

def age_checker(data, col1, col2):
    """
    Check if the temporal relationship is violated
    col1: the later time point
    col2: 
    
    """
    data[col1].replace('Null', np.nan, inplace = True)
    data[col2].replace('Null', np.nan, inplace = True)
    data[col1] = data[col1].astype(float)
    data[col2] = data[col2].astype(float)
    tmp = data[data[col1] < data[col2]]
    msg = ''
    if tmp.shape[0] >0:
        msg += '[ATTN] >>> {} records violate temporal relationship: `{}` is prior to `{}`. And the `system_patient_id` are: {}'.format(tmp.shape[0], col1, col2,tmp['system_patient_id'])
    else:
        msg += 'Success >>> the temporal relationship between `{}` and `{}` all pass.'.format(col1, col2)
    return msg



def align_col(df,table_source, dic):
    """ 
    align the column number and sequence the same as in the dic
    """
    dic_var = dic[dic['table_name'] == table_source].system_variable_name
    df = df[dic_var]
    return df