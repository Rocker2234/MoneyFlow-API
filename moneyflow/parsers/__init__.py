# USE THESE HEADERS ALWAYS for the resulting data after reading the uploaded file
FILE_HEADER = "txn_date,txn_desc,opr_dt,dbt_amount,cr_amount,ref_num,cf_amt"
CC_FILE_HEADER = "txn_date,txn_desc,amt,is_credit"

SUPPORTED_PARSERS = {
    "HDFC_D": ("HDFC Delimited", "%d/%m/%y"),
    "HDFC_CC_CSV": ("HDFC Credit Card CSV", "%d/%m/%y"),
    "ICICI_XLS": ("ICICI XLS Transaction History", "%d/%m/%Y"),
    "KTKB_XLS": ("Karnataka Bank XLS Transaction History", "%m/%d/%Y"),
    "NULL": ("DUMMY", "%d/%m/%Y"),
}
