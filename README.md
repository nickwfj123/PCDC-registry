# PCDC Registry

Authors: Fangjiang Wu, Yueqi Li, Hongyin Lai

## Introduction

This is a pipeline to preprocess raw clinical data and transform it to analysis-ready structures.

## Required Dependencies

- python = 3.7
- pandas = 1.3.5

<details>

  - _libgcc_mutex=0.1=main
  - _openmp_mutex=5.1=1_gnu
  - ca-certificates=2022.07.19=h06a4308_0
  - certifi=2022.6.15=py37h06a4308_0
  - ld_impl_linux-64=2.38=h1181459_1
  - libffi=3.3=he6710b0_2
  - libgcc-ng=11.2.0=h1234567_1
  - libgomp=11.2.0=h1234567_1
  - libstdcxx-ng=11.2.0=h1234567_1
  - ncurses=6.3=h5eee18b_3
  - openssl=1.1.1q=h7f8727e_0
  - pip=22.1.2=py37h06a4308_0
  - python=3.7.13=h12debd9_0
  - readline=8.1.2=h7f8727e_1
  - setuptools=63.4.1=py37h06a4308_0
  - sqlite=3.39.2=h5082296_0
  - tk=8.6.12=h1ccaba5_0
  - wheel=0.37.1=pyhd3eb1b0_0
  - xz=5.2.5=h7f8727e_1
  - zlib=1.2.12=h5eee18b_3
  - pip:
    - numpy==1.21.6
    - pandas==1.3.5
    - python-dateutil==2.8.2
    - pytz==2022.2.1
    - six==1.16.0
    
</details>


## Create Conda Environment

### Create environment from yml file

    conda env create -f env/etl.yml

### Manually create environment (optional)

install python and pandas

    conda create -n etl python=3.7
    conda activate etl
    pip install pandas==1.3.5

install ipykernel

    conda install -n etl ipykernel --update-deps --force-reinstall
    

## Processing Instructions

(Currently only for `reg_patient`)

### Step 1. Get the newest version pcdc_core folder into input folder

i.e., pcdc_core_folder/
- patient.csv
- biospecimen.csv
- pathology_image.csv

```
mv pcdc_core_folder your_path/input/pcdc_core_folder
```

### Step 2. Run `reg_patient_ose.py`
Input:
- `OSE_input_file`
- `map/codebook_mapping.csv`
- `im/dictionary.csv`
- `im/dictionary_codebook.csv`

Output:
- `reg_patient_ose.csv`

### Step 3. Run `reg_patient_rmse.py`
Input:
- `COG-RMS_input_file`
- `map/codebook_mapping.csv`
- `map/RMSE_col_map.csv`
- `im/dictionary.csv`
- `im/dictionary_codebook.csv`

Output:
- `reg_patient_rmse.csv`

### Step 4. Run `reg_patient_pdx.py`
Input:
- `PDX_DB_input_file`
- `map/PDC_DX_grouping.csv`
- `im/dictionary.csv`
- `im/dictionary_codebook.csv`

Output:
- `reg_patient_pdx.csv`

### Step 5. Run `reg_patient_gct.py`
Input:
- `GCTE_DB_input_file`
- `im/dictionary.csv`
- `im/dictionary_codebook.csv`

Output:
- `reg_patient_gct.csv`

### Step 6. Run `reg_patient_mda.py`
Input:
- `PSTCDRC01_input_file`
- `map/mp_dx.xlsx`
- `im/dictionary.csv`
- `im/dictionary_codebook.csv`

Output:
- `reg_patient_mda.csv`

### Step 7. Run `reg_patient_merge.py`
Merge all subtables and generate final output.

`merge_checkers.txt` to record any data QC issue.

Input:
- `pcdc_core_folder`
- `reg_patient_ose.csv`
- `reg_patient_rmse.csv`
- `reg_patient_pdx.csv`
- `reg_patient_gct.csv`
- `reg_patient_mda.csv`
- `im`

Output:
- `reg_patient_merge.csv`
- `merge_checkers.txt`


## Functions Comparison Table

|Function Name      |<div align="center">PCDC Public Registry</div>    |<div align="center">PCDC Core Data</div>  |Description       |
|-------------------|:-----------------------:|:------------------:|------------------|
|map_multiple_cols  |:heavy_check_mark:       |:heavy_check_mark:  |Map multiple source column names and values with destination ones |
|map_single_col     |:heavy_check_mark:       |:heavy_check_mark:  |Map single column in source table |
|calculate_date     |:heavy_check_mark:       |:heavy_check_mark:  |Calculate the difference between two dates |
|calculate_age      |:heavy_check_mark:       |:x:                 |Calculate the difference between two ages
|check_add_cols     |:heavy_check_mark:       |:x:                 |Checker for cols and add missing columns
|create_id_col      |:heavy_check_mark:       |:x:                 |Create system_patient_id col
|add_record_id      |:heavy_check_mark:       |:heavy_check_mark:  |Make utsw_pcdc_id unique for one record if one patient has duplicated record |
|dic_cb_checker     |:heavy_check_mark:       |:heavy_check_mark:  |Check if the value in the output column is not includedin the corresponding value in the dictionary_codebook file |
|null_val_checker   |:heavy_check_mark:       |:heavy_check_mark:  |Check if there is null value in not nullable columns according to dictionary file |
|pick_notin         |:x:                      |:heavy_check_mark:  |Pick the element that in the a but not in the b |
|checker_dictionary |:x:                      |:heavy_check_mark:  |Check if columns and variables from the script output are all included in the information model |
|id_match           |:x:                      |:heavy_check_mark:  |Check if 1:1 match works between two columns |                                                                                   
