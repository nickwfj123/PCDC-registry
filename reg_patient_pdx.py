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
    pat = pd.read_csv(args['PDX'] + 'patient.csv')
    proc = pd.read_csv(args['PDX'] + 'proc.csv')
    img = pd.read_csv(args['PDX'] + 'image.csv')
    sample = pd.read_csv(args['PDX'] + 'sample.csv')

    dic  = pd.read_csv("im/dictionary.csv", dtype=object)
    dic_cb = pd.read_csv("im/dictionary_codebook.csv")
    dx_map = pd.read_csv('map/PDX_DX_grouping.csv')
    
    pdx_tab = pd.DataFrame(columns={'utsw_pcdc_id','source_project_patient_id'})
    pdx_tab['source_project_patient_id'] = pat['PatientID']
    pdx_tab['utsw_pcdc_id'] = 'PCDC_PDX_' + pdx_tab['source_project_patient_id']

    pat = pat.rename(columns={'age_diagnosis_year':'age_diagnosis','metastasis_at_diagnosis':'metastasis_diagnosis'})
    cols = ['PatientID','sex', 'race', 'ethnicity', 'age_diagnosis','diagnosis_final', 'metastasis_diagnosis']
    # merge demographics
    pdx_tab = pd.merge(pdx_tab, pat[cols], left_on='source_project_patient_id', right_on='PatientID', how='left')
    # merge dx_group
    dx_map = dx_map.rename(columns={'Primary diagnosis_level 1':'dx_group', 'level 2':'diagnosis_final'})

    # fill NaN in dx_group col
    for index, value in enumerate(dx_map['dx_group']):
        if index > 0:
            if not pd.isna(value):
                tmp = value
            else:
                dx_map['dx_group'][index] = tmp

    pdx_tab = pd.merge(pdx_tab, dx_map, on='diagnosis_final', how='left')
    pdx_tab['dx_group'] = pdx_tab['dx_group'].str.strip()

    # join tables
    sample = pd.merge(sample, proc[['sys_procedure_id','PatientID']], on='sys_procedure_id', how='left')
    img = pd.merge(img, sample[['sys_sample_id','sys_procedure_id','PatientID']], on='sys_sample_id', how='left')
    
    # create pr image table
    pr = pd.DataFrame(columns=['PatientID','pathimg'])
    pr['PatientID'] = img['PatientID'].unique()
    pr['pathimg'] = 'Yes'
    img_count = img['PatientID'].value_counts().rename_axis('PatientID').reset_index(name='n_pathimg')
    pr = pd.merge(pr, img_count, on='PatientID', how='left')
    
    # merge image to pdx_tab
    pdx_tab = pd.merge(pdx_tab, pr, on='PatientID', how='left')
    pdx_tab['pathimg'] = pdx_tab['pathimg'].fillna('No')
    pdx_tab['n_pathimg'] = pdx_tab['n_pathimg'].fillna(0)
    pdx_tab['n_pathimg'] = pdx_tab['n_pathimg'].astype(int)
    
    # select columns
    select_col = pdx_tab.columns[pdx_tab.columns.isin(dic['system_variable_name'])]
    reg_pdx = pdx_tab[select_col]
    reg_pdx['source_project'] = 'Pediatric PDX Explorer'
    reg_pdx = reg_pdx[reg_pdx['dx_group']!= 'Normal tissue/no tumor']
    
    # add data_version col
    today = date.today()
    d = today.strftime("%Y%m%d")
    reg_pdx['data_version'] = 'pcdc_reg_v' + d

    # check if values are matched with dic_cb and dic
    print(dic_cb_checker(reg_pdx, dic_cb))
    print(null_val_checker(reg_pdx, dic))

    output_path = args['output'] + d + '_reg_patient_output/'
    if not os.path.exists(output_path):
        os.mkdir(output_path)
    
	# output: result file, config file and current python script
    reg_pdx.to_csv(output_path + 'reg_patient_pdx.csv', index=False, na_rep='NULL')
    
    with open(output_path + 'config_pdx.txt', "w") as f:
        print("### This is a record file for the paths of input files ### \n", file = f)
        print("PDX: " + args['PDX'] + '\n', file = f)
    
    with open(__file__, 'r') as f:
        with open(output_path + 'script_pdx.py', 'w') as out:
            for line in (f.readlines()):
                print(line, end='', file=out)

    
if __name__ == "__main__":
    args = {
        "PDX": PDX,
        "output": output,
    }
    main(args)
