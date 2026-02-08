import csv
from io import StringIO, BufferedReader

import xlrd

FILE_HEADER = "opr_dt,txn_date,ref_num,txn_desc,dbt_amount,cr_amount,cf_amt"


def parse_xls(uploaded_file: BufferedReader) -> str:
    workbook = xlrd.open_workbook(file_contents=uploaded_file.read())
    sheet = workbook.sheet_by_index(0)
    rows = FILE_HEADER + '\n'

    for row_idx in range(13, sheet.nrows):
        row = sheet.row(row_idx)
        this_row = ''

        if row[1].value.startswith("Legends"):
            break

        for cell in row[2:9]:
            this_row += cell.value + ','

        this_row = this_row.removesuffix(',')
        this_row = list(csv.reader(StringIO(this_row)))[0]
        txn_desc = this_row[3]
        this_row[2] = txn_desc.split('/')[5]
        rows += ','.join(this_row) + '\n'
    return rows


if __name__ == '__main__':
    with open('Examples/ICICI_TxnHist.xls', 'rb') as f:
        with open('temp.csv', 'w', newline='') as csvfile:
            csvfile.writelines(parse_xls(f))
