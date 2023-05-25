import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

from datetime import date
from config import *
from functions import *

def main(args):
    # load data
    cog = pd.read_csv(args["RMS"] + "cog_clinical_curated.csv")
    instructa = pd.read_csv(args["RMS"] + "instruct_a_curated.csv")
    instructb = pd.read_csv(args["RMS"] + "instruct_b_curated.csv")
    path_img = pd.read_csv(args["RMS"] + "pathology_image.csv")
    hist_map = pd.read_csv(args["RMS"] + "mapping_histology_rms.csv")

    col_file = pd.read_csv("map/RMSE_col_map.csv")
    dic = pd.read_csv("im/dictionary.csv", dtype=object)
    dic_cb = pd.read_csv("im/dictionary_codebook.csv", dtype=object)
    mapper = pd.read_csv('map/codebook_mapping.csv')
    
    temp = path_img[['source_filename','patient_usi']]
    temp['patient_usi'] = temp['patient_usi'].str.strip()
    # select patients that have img data
    pat_list = path_img.loc[(path_img['patient_usi'].isin(instructa['patient_usi'])) | (path_img['patient_usi'].isin(cog['patient_usi'])), 'patient_usi']
    # create pathology table
    temp = temp[temp['patient_usi'].isin(pat_list)]

    pr = pd.DataFrame(columns=['patient_usi'])
    pr['patient_usi'] = temp['patient_usi'].unique()
    pr['pathimg'] = 'Yes'
    # count image
    img_count = temp['patient_usi'].value_counts().rename_axis('patient_usi').reset_index(name='n_pathimg')
    pr = pd.merge(pr, img_count, on='patient_usi', how='left')
    pr = pr.rename(columns={"patient_usi": "source_project_patient_id"})

    # select columns
    cog_col = cog.columns[cog.columns.isin(col_file['COG'])]
    df_cog = cog[cog_col]
    
    instructa_col = instructa.columns[instructa.columns.isin(col_file['INSTRUCT'])]
    df_instructa = instructa[instructa_col]
    
    instructb_col = instructb.columns[instructb.columns.isin(col_file['INSTRUCT'])]
    df_instructb = instructb[instructb_col]
    df_instructb['patient_usi'] = df_instructb['patient_usi'].str.strip()

    # calculate age
    df_cog = calculate_age(df_cog, 'age_at_enrollment_days', 'age_diagnosis')
    df_cog = calculate_age(df_cog, 'age_at_event', 'age_first_event')
    df_cog = calculate_age(df_cog, 'age_at_follow_up', 'age_last_followup')

    df_instructa = calculate_age(df_instructa, 'age_at_diagnosis', 'age_diagnosis')
    df_instructa = calculate_age(df_instructa, 'age_at_event', 'age_first_event')
    df_instructa = calculate_age(df_instructa, 'age_at_follow_up', 'age_last_followup')

    df_cog['last_vital_status'] = np.nan
    df_cog.loc[df_cog['age_at_death'].notna(),'last_vital_status'] = 'Dead'
    df_cog['last_vital_status'] = df_cog['last_vital_status'].fillna('Alive') 

    df_instructa['last_vital_status'] = np.nan
    df_instructa.loc[df_instructa['age_at_death'].notna(),'last_vital_status'] = 'Dead'
    df_instructa['last_vital_status'] = df_instructa['last_vital_status'].fillna('Alive')

    # execute mapper
    df_cog = map_multiple_cols(df_cog, mapper, 'COG')
    df_instructa = map_multiple_cols(df_instructa, mapper, 'INSTRUCT')
    df_instructb = map_multiple_cols(df_instructb, mapper, 'INSTRUCT')

    # identify patients that have multiple events/rows
    df_instructb['multiple_events'] = np.nan
    df_instructb.loc[df_instructb['source_project_patient_id'].duplicated(keep=False),'multiple_events']='Yes'
    df_instructb['multiple_events'] = df_instructb['multiple_events'].fillna('No')  
    df_instructb.loc[df_instructb['multiple_events']=='Yes', 'first_event_type']='Event, NOS'
    df_instructb = df_instructb.drop_duplicates()
    
    # merge df_instructa and df_instructb
    df_instruct = pd.merge(df_instructa, df_instructb, on=['utsw_pcdc_id','source_project_patient_id'], how='left')
    df_instruct = pd.merge(df_instruct, hist_map[['source_value','dx_code','dx_name']], left_on='patient_histology', right_on='source_value', how='left')
    df_cog = pd.merge(df_cog, hist_map[['source_value','dx_code','dx_name']], left_on='patient_histology', right_on='source_value', how='left')  
    
    # create RMS table
    reg_patient_cols = col_file['reg_patient'].dropna()
    df_cog = df_cog[df_cog.columns[df_cog.columns.isin(reg_patient_cols)]]
    df_instruct = df_instruct[df_instruct.columns[df_instruct.columns.isin(reg_patient_cols)]] 

    rms_tab = pd.DataFrame(columns=reg_patient_cols)
    rms_list = [rms_tab, df_cog, df_instruct]
    rms_tab = pd.concat(rms_list)
    
    rms_tab['source_project'] = 'Rhabdomyosarcoma Explorer'
    rms_tab['dx_vocab'] = 'ICD-O-3.1 (customized)'
    rms_tab['dx_group'] = 'Rhabdomyosarcoma' 
    rms_tab = rms_tab.drop(columns=['pathimg','n_pathimg'])
    
    rms_tab = pd.merge(rms_tab, pr, on='source_project_patient_id', how='left') 
    
    rms_tab['pathimg'] = rms_tab['pathimg'].fillna('No')
    rms_tab['n_pathimg'] = rms_tab['n_pathimg'].fillna(0)
    rms_tab['n_pathimg'] = rms_tab['n_pathimg'].astype(int)

    # add data_version col
    today = date.today()
    d = today.strftime("%Y%m%d")
    rms_tab['data_version'] = 'pcdc_reg_v' + d

    # check if values are matched with dic_cb and dic
    print(dic_cb_checker(rms_tab, dic_cb))
    print(null_val_checker(rms_tab, dic))
    
    # create output folder if not exists
    today = date.today()
    d = today.strftime("%Y%m%d")

    output_path = args['output'] + d + '_reg_patient_output/'
    if not os.path.exists(output_path):
        os.mkdir(output_path)
        
    # output: result file, config file and current python script
    rms_tab.to_csv(output_path + 'reg_patient_rmse.csv', index=False, na_rep='NULL')
    
    with open(output_path + 'config_rmse.txt', "w") as f:
        print("### This is a record file for the paths of input files ### \n", file = f)
        print("RMS: " + args['RMS'] + '\n', file = f)

    with open(__file__, 'r') as f:
        with open(output_path + 'script_rmse.py', 'w') as out:
            for line in (f.readlines()):
                print(line, end='', file=out)
            

if __name__ == "__main__":
    args = {
        "RMS": RMS,
        "output": output,
    }
    main(args)
