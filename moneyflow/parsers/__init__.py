# USE THIS HEADER ALWAYS for the resulting data after reading the uploaded file
FILE_HEADER = "txn_date,txn_desc,opr_dt,dbt_amount,cr_amount,ref_num,cf_amt"

SUPPORTED_PARSERS = {
    "HDFC_D": "HDFC Delimited",
    "NULL": "DUMMY",
}
