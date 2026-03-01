import warnings
from io import BufferedReader, BytesIO

import msoffcrypto
import openpyxl

FILE_HEADER = "opr_dt,txn_date,txn_desc,ref_num,dbt_amount,cr_amount,cf_amt"


def unlock_file(uploaded_file: BufferedReader, pw: str) -> BytesIO:
    file = BytesIO()
    try:
        orgnl_file = msoffcrypto.OfficeFile(uploaded_file)
        orgnl_file.load_key(password=pw)
        orgnl_file.decrypt(file)
    except msoffcrypto.exceptions.InvalidKeyError:
        raise ValueError("Invalid Document Password")
    return file


def parse_xlsx(uploaded_file: BufferedReader, pw: str) -> str:
    file = unlock_file(uploaded_file, pw)

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
        workbook = openpyxl.load_workbook(file, read_only=True, data_only=True)
        sheet = workbook.active
    rows = FILE_HEADER + '\n'

    for row in tuple(sheet.rows)[18:]:
        if not row[0].value:
            break
        this_row = ''

        # opr_dt,txn_date are assumed to be the same
        this_row += row[0].value + ','
        this_row += row[0].value + ','

        # txn_desc
        txn_desc: str = row[1].value.replace('\n ', '').strip()
        this_row += txn_desc + ','

        # ref_num
        try:
            if txn_desc.find("UPI/") >= 0:
                this_row += txn_desc.split('/')[2]
            if txn_desc.strip().startswith("CEMTEX"):
                this_row += txn_desc.split('   ')[1].split(' ')[1]
            if txn_desc.strip().startswith("CSH"):
                this_row += txn_desc.split('   ')[1].split(' ')[0]
            if txn_desc.split('*')[0].endswith('NEFT'):
                this_row += txn_desc.split('   ')[1].split('*')[2]
        except IndexError:
            pass
        finally:
            this_row += ','

        # dbt_amount,cr_amount,cf_amt
        dbt_amount = row[3].value
        if not dbt_amount:
            dbt_amount = "0.00"
        cr_amount = row[4].value
        if not cr_amount:
            cr_amount = "0.00"
        cf_amt = row[5].value
        if not cf_amt:
            cf_amt = "0.00"
        this_row += dbt_amount + ','
        this_row += cr_amount + ','
        this_row += cf_amt

        rows += this_row + '\n'
    return rows


if __name__ == '__main__':
    with open('Examples/SBI_XLSX.xlsx', 'rb') as f:
        with open('Examples/temp.csv', 'w', newline='') as csvfile:
            csvfile.writelines(parse_xlsx(f, "TEST"))
