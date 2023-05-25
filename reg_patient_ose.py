import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

from datetime import date
from config import *
from functions import *

def main(args):
    # load data file
    ose = pd.read_csv(args['OSE'] + 'clinical.csv')

    dic = pd.read_csv("im/dictionary.csv", dtype=object)
    dic_cb = pd.read_csv("im/dictionary_codebook.csv", dtype=object)
    mapper = pd.read_csv('map/codebook_mapping.csv')

    # select ose columns
    col_os = ['utsw_pcdc_id', 'system_patient_id', 'Gender', 'Race', 'Ethnicity',
       'Age at Diagnosis','Age at Diagnosis in Days', 'First Event', 'Time to First Event in Days','Vital Status',
       'Overall Survival Time in Days','Disease at diagnosis', 'Age at Enrollment in Days','data_source','data_version']
    temp = ose[col_os]

    # create age_diagnosis
    temp['age_diagnosis'] = temp['Age at Diagnosis in Days']
    temp.loc[temp['age_diagnosis'].isnull(),'age_diagnosis'] = temp.loc[temp['age_diagnosis'].isnull(),'Age at Enrollment in Days']
    
    temp['age_first_event'] =  ((temp['age_diagnosis'] + temp['Time to First Event in Days'])/365).round(1)
    temp['age_last_followup'] = ((temp['age_diagnosis'] + temp['Overall Survival Time in Days'])/365).round(1)
    temp['age_diagnosis'] = (temp['age_diagnosis']/365).round(1)

    # map destination variable
    temp = map_multiple_cols(temp, mapper, 'os')

    # create os table
    cols=['utsw_pcdc_id', 'source_project_patient_id', 'sex', 'race', 'ethnicity',
       'age_diagnosis', 'age_last_followup','age_first_event','first_event_type','last_vital_status','metastasis_diagnosis']
    os_tab = temp[cols]

    os_tab['source_project'] = 'Osteosarcoma Explorer'
    os_tab['dx_vocab'] = 'ICD-O-3.1 (customized)'
    os_tab['dx_group'] = 'Osteosarcoma'
    os_tab['dx_code'] = '9180/3'
    os_tab['dx_name'] = 'Osteosarcoma, NOS'

    # assign image status
    os_tab['pathimg']=np.nan
    os_tab.loc[os_tab['utsw_pcdc_id'].str.startswith('UTSW_'), 'pathimg']='Yes'
    os_tab['pathimg'] = os_tab['pathimg'].fillna('No')
    
    # assign image count
    os_tab['n_pathimg']=np.nan
    os_tab.loc[os_tab['utsw_pcdc_id'].str.startswith('UTSW_'),'n_pathimg']= 1
    os_tab['n_pathimg']= os_tab['n_pathimg'].fillna(0)
    os_tab['n_pathimg'] = os_tab['n_pathimg'].astype(int)

    # add data_version col
    today = date.today()
    d = today.strftime("%Y%m%d")
    os_tab['data_version'] = 'pcdc_reg_v' + d

    # check if values are matched with dic_cb and dic
    print(dic_cb_checker(os_tab, dic_cb))
    print(null_val_checker(os_tab, dic))

    # create output folder if not exists
    output_path = args['output'] + d + '_reg_patient_output/'
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    
	# output: result file, config file and current python script
    os_tab.to_csv(output_path + 'reg_patient_ose.csv', index=False, na_rep='NULL')
    
    with open(output_path + 'config_ose.txt', "w") as f:
        print("### This is a record file for the paths of input files ### \n", file = f)
        print("OSE: " + args['OSE'] + '\n', file = f)
    
    with open(__file__, 'r') as f:
        with open(output_path + 'script_ose.py', 'w') as out:
            for line in (f.readlines()):
                print(line, end='', file=out)
    
if __name__ == "__main__":
    args = {
        "OSE": OSE,
        "output": output,
    }
    
    main(args)
