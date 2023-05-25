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
    pat = pd.read_csv(args["GCT"] + "gct_table_Patients.csv", dtype=object)
    gender = pd.read_csv(args["GCT"] + "gct_table_CodeGender.csv", dtype=object)
    followup = pd.read_csv(args["GCT"] + "gct_table_Followup.csv", dtype=object)
    diagnosis = pd.read_csv(args["GCT"] + "gct_table_TumorDiagnosis.csv", dtype=object)
    
    dic = pd.read_csv("im/dictionary.csv", dtype=object)
    dic_cb = pd.read_csv("im/dictionary_codebook.csv", dtype=object)
    
    pat = pat[["PatientID", "OldPatientID", "Gender", "Race", "AgeAtDiagnosis_year"]]
    
    # gender
    gender = gender.rename(columns={'ID': 'Gender'})
    pat = map_single_col(pat, 'Gender', gender, 'Initial')
    pat['Gender'].fillna('Unknown', inplace=True)
    
    # followup
    followup = followup[["FollowupID", "PatientID", "DateFollowup", "Death"]] ## followup ID -> ???
    pat = pd.merge(pat, followup, how="left", on=["PatientID"])
    death_dic = {'0':'Dead', '1':'Alive', np.nan:'Unknown'}
    pat['Death'] = pat['Death'].map(death_dic)
    
    # diagnosis
    diagnosis = diagnosis[["TumorDiagnosisID","PatientID","DateDiagnosis","Site"]] ## TumorDiagnosisID -> ???
    pat = pd.merge(pat, diagnosis, how="left", on=["PatientID"])
    
    # calculate age at last follow-up
    pat['DateFollowup'] = pd.to_datetime(pat['DateFollowup'])
    pat['DateDiagnosis'] = pd.to_datetime(pat['DateDiagnosis'])
    pat['diff_year'] = calculate_date(pat, 'DateFollowup', 'DateDiagnosis')
    
    pat['age_last_followup'] = np.nan
    pat['AgeAtDiagnosis_year'] = pd.to_numeric(pat['AgeAtDiagnosis_year']).round(1)
    
    pat.loc[pat['diff_year'] != np.nan, 'age_last_followup'] = pat['AgeAtDiagnosis_year'] + pat['diff_year']
    
    # rename col headers
    pat = pat.rename(columns={'PatientID':'source_project_patient_id', 'Gender':'sex', 'Race':'race', 
    'AgeAtDiagnosis_year':'age_diagnosis', 'Death':'last_vital_status'})
    
    # add missing columns
    pat['ethnicity'] = np.nan
    pat['dx_group'] = "Germ cell tumor"
    pat['metastasis_diagnosis'] = np.nan
    pat['pathimg'] = np.nan
    pat['n_pathimg'] = np.nan
    pat['source_project'] = 'Germ Cell Tumor Explorer'
    
    pat['utsw_pcdc_id'] = 'PCDC_GCTE_' + pat['source_project_patient_id'].astype(str)
    
    pat = pat[['utsw_pcdc_id', 'source_project_patient_id', 'sex', 'race', 'ethnicity', 'age_last_followup', 
    'last_vital_status', 'age_diagnosis', 'dx_group', 'metastasis_diagnosis', 'pathimg', 'n_pathimg', 'source_project']]
    
    # add data_version col
    today = date.today()
    d = today.strftime("%Y%m%d")
    pat['data_version'] = 'pcdc_reg_v' + d

    # check if values are matched with dic_cb and dic
    print(dic_cb_checker(pat, dic_cb))
    print(null_val_checker(pat, dic))

    # create the output folder and file
    output_path = args['output'] + d + '_reg_patient_output/'
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    # output result file, config file and current python script
    pat.to_csv(output_path + 'reg_patient_gct.csv', index=False, na_rep='NULL')
    
    with open(output_path + 'config_gct.txt', "w") as f:
        print("### This is a record file for the paths of input files ### \n", file = f)
        print("GCT: " + args['GCT'] + '\n', file = f)

    with open(__file__, 'r') as f:
        with open(output_path + 'script_gct.py', 'w') as out:
            for line in (f.readlines()):
                print(line, end='', file=out)

if __name__ == "__main__":
    args = {
        'GCT': GCT,
        'output': output,
    }

    main(args)
