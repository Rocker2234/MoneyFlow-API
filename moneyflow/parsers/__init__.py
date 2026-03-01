# USE THESE HEADERS ALWAYS for the resulting data after reading the uploaded file
FILE_HEADER = "txn_date,txn_desc,opr_dt,dbt_amount,cr_amount,ref_num,cf_amt"
CC_FILE_HEADER = "txn_date,txn_desc,amt,is_credit"


# A Dict of supported parsers with Parser name as keys and
# values as tuples containing Name, Date Format, isPasswordProtected fields respectively.
SUPPORTED_PARSERS = {
    "HDFC_D": ("HDFC Delimited", "%d/%m/%y", False),
    "HDFC_CC_CSV": ("HDFC Credit Card CSV", "%d/%m/%y", False),
    "ICICI_XLS": ("ICICI XLS Transaction History", "%d/%m/%Y", False),
    "KTKB_XLS": ("Karnataka Bank XLS Transaction History", "%m/%d/%Y", False),
    "SBI_XLSX": ("SBI XLSX Transaction History", "%d/%m/%Y", True),
    "NULL": ("DUMMY", "%d/%m/%Y", False),
}
