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
    mda = pd.read_csv(args["MDA"] + "clinical.csv", dtype=object)
    mda_map = pd.read_excel("map/mp_dx.xlsx", dtype=object)

    dic = pd.read_csv("im/dictionary.csv", dtype=object)
    dic_cb = pd.read_csv("im/dictionary_codebook.csv", dtype=object)

    # create utsw_pcdc_id    
    mda['utsw_pcdc_id'] = mda.index + 1
    mda['utsw_pcdc_id'] = mda['utsw_pcdc_id'].astype('string').apply(lambda x: 'PCDC_MDA' + x.zfill(6))

    # create metastasis_diagnosis
    mda.loc[mda['Stage at dx']=='Localized', 'metastasis_diagnosis'] = 'No'
    mda.loc[mda['Stage at dx']=='Metastatic', 'metastasis_diagnosis'] = 'Yes'
    mda.loc[mda['Stage at dx']=='Null', 'metastasis_diagnosis'] = np.nan

    # map values
    mda.loc[mda['Race']=='White or Caucasian', 'Race'] = 'White'
    mda.loc[mda['Ethnicity']=='non-hispanic', 'Ethnicity'] = 'Not Hispanic or Latino'
    mda.loc[mda['Ethnicity']=='Hispanic', 'Ethnicity'] = 'Hispanic or Latino'
    mda.loc[mda['Ethnicity']=='Patient refused', 'Ethnicity'] = 'Unknown'
    mda.loc[mda['Vital_Status']=='Null', 'Vital_Status'] = 'Unknown'

    # map dx_group
    map_single_col(mda, 'Histology', mda_map, 'dx_group')
    
    # rename col headers
    mda = mda.rename(columns={'PEDS ID':'source_project_patient_id', 'Sex':'sex', 'Race':'race', 'Ethnicity':'ethnicity', 
    'Vital_Status':'last_vital_status', 'Age_Primary_Diagnosis':'age_diagnosis', 'Histology':'dx_group'})
    
    # add missing columns
    mda['age_last_followup'] = np.nan
    mda['pathimg'] = np.nan
    mda['n_pathimg'] = np.nan
    mda['source_project'] = 'CPRIT Pediatric Solid Tumors Comprehensive Data Resource Core (MDACC)'

    mda = mda[['utsw_pcdc_id', 'source_project_patient_id', 'sex', 'race', 'ethnicity', 'age_last_followup', 
    'last_vital_status', 'age_diagnosis', 'dx_group', 'metastasis_diagnosis', 'pathimg', 'n_pathimg', 'source_project']]

    # add data_version col
    today = date.today()
    d = today.strftime("%Y%m%d")
    mda['data_version'] = 'pcdc_reg_v' + d

    # check if values are matched with dic_cb and dic
    print(dic_cb_checker(mda, dic_cb))
    print(null_val_checker(mda, dic))

    # create the output folder and file
    output_path = args['output'] + d + '_reg_patient_output/'
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # output result file, config file and current python script
    mda.to_csv(output_path + 'reg_patient_mda.csv', index=False, na_rep='NULL')
    
    with open(output_path + 'config_mda.txt', "w") as f:
        print("### This is a record file for the paths of input files ### \n", file = f)
        print("MDA: " + args['MDA'] + '\n', file = f)

    with open(__file__, 'r') as f:
        with open(output_path + 'script_mda.py', 'w') as out:
            for line in (f.readlines()):
                print(line, end='', file=out)

if __name__ == "__main__":
    args = {
        'MDA': MDA,
        'output': output,
    }

    main(args)
