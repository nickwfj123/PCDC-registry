from functions import *
from config import *
from datetime import date
from functools import reduce
from ast import arg
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")


def main(args):
    # load the data
    base = pd.read_csv(args["base"] + 'patient.csv')
    ose = pd.read_csv(output_path + 'reg_patient_ose.csv')
    rms = pd.read_csv(output_path + 'reg_patient_rmse.csv')
    pdx = pd.read_csv(output_path + 'reg_patient_pdx.csv')
    gct = pd.read_csv(output_path + 'reg_patient_gct.csv')
    mda = pd.read_csv(output_path + 'reg_patient_mda.csv')
    specimen = pd.read_csv(args["base"] + 'biospecimen.csv', dtype=object)
    path_img = pd.read_csv(args["base"] + 'pathology_image.csv', dtype=object)

    dic = pd.read_csv("im/dictionary.csv")
    dic_cb = pd.read_csv("im/dictionary_codebook.csv")

    # [update] auto-complete based on input data version of patient table
    base['data_version'] = args["base"].split(sep='/')[-2]

    ## add content for n_pathimg and pathimg
    path_img = path_img['pcdc_patient_id'].value_counts().rename_axis('pcdc_patient_id').reset_index(name='n_pathimg')
    specimen = specimen.merge(path_img, how='left', on='pcdc_patient_id').rename(columns={'availability_pathimg':'pathimg'})
    cols = ['pcdc_patient_id', 'pathimg', 'n_pathimg']
    specimen = specimen[cols].dropna(subset=['pathimg']).drop_duplicates()

    base = base.merge(specimen, how='left', on='pcdc_patient_id')

    # Select registry cohort
    # pat_list = cohort_all.loc[cohort_all['cohort_registry'] == 'Yes', 'qbrc_patient_id']
    # base = base[base['utsw_pcdc_id'].isin(pat_list)].reset_index(drop=True)
    base['source_project_patient_id'] = base['pcdc_patient_id']
    base['source_project'] = "PCDC Children's Health"

    # ## [update: rename pcdc_patient_id to match append method for following sources]
    # base.rename(columns={'pcdc_patient_id':'utsw_pcdc_id'},inplace=True)

    # Add missing cols
    reg_patient = check_add_cols(base, dic)

    # Create system patient id
    new_id_col = "system_patient_id"  # the newly created system patient id
    new_col_prefix = "PCDC_P"  # format of id: PCDC_P000001
    size_num = 6  # this is the size of the number for the id; e.g. PCDC_P000001, we have 6 numbers after prefix
    # the id col used to create a system patient id (identify unique patients in source data)
    map_id_col = "source_project_patient_id"

    reg_patient = create_id_col(
        reg_patient, new_id_col, map_id_col, new_col_prefix, size_num)

    # record_id_col = 'utsw_pcdc_id'  # set up duplicated record ID col name
    # record_suffix = '_Dx'  # set duplicated record suffix
    # reg_patient = add_record_id(reg_patient, record_id_col, record_suffix)

    # Append OSE data
    ose.rename(columns={'utsw_pcdc_id':'pcdc_patient_id'}, inplace=True)
    reg_patient = reg_patient.append(
        ose, ignore_index=True)  # add new system patient id
    reg_patient = create_id_col(
        reg_patient, new_id_col, map_id_col, new_col_prefix, size_num)

    # Apppend RMSE re
    rms.rename(columns={'utsw_pcdc_id':'pcdc_patient_id'}, inplace=True)
    reg_patient = reg_patient.append(
        rms, ignore_index=True)  # add new system patient id
    reg_patient = create_id_col(
        reg_patient, new_id_col, map_id_col, new_col_prefix, size_num)

    # Append PDX data
    pdx.rename(columns={'utsw_pcdc_id':'pcdc_patient_id'}, inplace=True)
    reg_patient = reg_patient.append(
        pdx, ignore_index=True)  # add new system patient id
    reg_patient = create_id_col(
        reg_patient, new_id_col, map_id_col, new_col_prefix, size_num)

    # Append GCTE data
    gct.rename(columns={'utsw_pcdc_id':'pcdc_patient_id'}, inplace=True)
    reg_patient = reg_patient.append(
        gct, ignore_index=True)  # add new system patient id
    reg_patient = create_id_col(
        reg_patient, new_id_col, map_id_col, new_col_prefix, size_num)

    # Append MDA data
    mda.rename(columns={'utsw_pcdc_id':'pcdc_patient_id'}, inplace=True)
    reg_patient = reg_patient.append(
        mda, ignore_index=True)  # add new system patient id
    reg_patient = create_id_col(
        reg_patient, new_id_col, map_id_col, new_col_prefix, size_num)

 
    ##[update] change the 'utsw-id' to 'pcdc_pateint_id" in the last step
    reg_patient.rename(columns = {'utsw_pcdc_id':'pcdc_patient_id'}, inplace = True)
    reg_patient = align_col(reg_patient,'reg_patient', dic)

    ##[update] for data quality check
    reg_patient.drop_duplicates(inplace = True)
    # strip() for our final output
    reg_patient = reg_patient.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    
    # save reg_patient.csv
    reg_patient.to_csv(output_path + 'reg_patient_merge.csv',
                       index=False, na_rep='NULL')

    with open(output_path + 'config_merge.txt', "w") as f:
        print("### This is a record file for the paths of input files ### \n", file=f)
        print("base: " + args['base'] + '\n', file=f)
        print("output_path: " + args['output'] + '\n', file=f)

    with open(__file__, 'r') as f:
        with open(output_path + 'script_merge.py', 'w') as out:
            for line in (f.readlines()):
                print(line, end='', file=out)

    with open(output_path + 'merge_checkers.txt',"w") as f:
        print("\n ### Result of checkers to generate reg_patient_merge.csv### ", file = f)
        print('\n The result of IM dictionary check is \n >>>',checker_dictionary(reg_patient,'reg_patient',dic),file = f)
        print('\n The result of dictionary codebook value match is  \n >>>',dic_cb_checker(reg_patient,dic_cb),file = f)
        print('\n The result of ID match checker is  \n >>>',one_to_many_id(reg_patient,'system_patient_id','source_project_patient_id'),file = f)
        print('\n The result of ID match checker is  \n >>>',one_to_many_id(reg_patient,'system_patient_id','pcdc_patient_id'),file = f)
        print('\n The check of age temporal relatinship is  \n >>>',age_checker(reg_patient, 'age_last_followup','age_diagnosis'), file = f)
        print('\n >>>', age_checker(reg_patient, 'age_last_followup','age_first_event'), file = f)
        print('\n >>>', age_checker(reg_patient, 'age_last_followup','age_first_visit'), file = f)





if __name__ == "__main__":

    today = date.today()
    d = today.strftime("%Y%m%d")
    output_path = output + d + '_reg_patient_output/'

    if not os.path.exists(output_path):
        os.mkdir(output_path)

    args = {
        "base": base,
        "output": output_path
    }
    main(args)
