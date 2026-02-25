from io import BufferedReader

import xlrd

FILE_HEADER = "opr_dt,txn_date,ref_num,txn_desc,dbt_amount,cr_amount,cf_amt"


def parse_xls(uploaded_file: BufferedReader) -> str:
    workbook = xlrd.open_workbook(file_contents=uploaded_file.read())
    sheet = workbook.sheet_by_index(0)
    rows = FILE_HEADER + '\n'

    for row in tuple(sheet.get_rows())[17:]:
        this_row = ''

        # opr_dt,txn_date are assumed to be the same
        this_row += row[2].value.replace(',', '/') + ','
        this_row += row[2].value.replace(',', '/') + ','

        # ref_num
        if row[5].value.startswith("UPI"):
            this_row += row[5].value.split(':')[1]
        this_row += ','

        # txn_desc
        this_row += row[5].value.replace(',', '~') + ','

        # dbt_amount,cr_amount,cf_amt
        dbt_amount = row[11].value.replace(',', '')
        if not dbt_amount:
            dbt_amount = "0.00"
        cr_amount = row[13].value.replace(',', '')
        if not cr_amount:
            cr_amount = "0.00"
        cf_amt = row[16].value.replace(',', '')
        if not cf_amt:
            cf_amt = "0.00"
        this_row += dbt_amount + ','
        this_row += cr_amount + ','
        this_row += cf_amt

        rows += this_row + '\n'
    return rows


if __name__ == '__main__':
    with open('Examples/KTKB_XLS.xls', 'rb') as f:
        with open('temp.csv', 'w', newline='') as csvfile:
            csvfile.writelines(parse_xls(f))
