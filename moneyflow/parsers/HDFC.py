from io import BufferedReader, TextIOWrapper

FILE_HEADER = "txn_date,txn_desc,opr_dt,dbt_amount,cr_amount,ref_num,cf_amt"
CC_FILE_HEADER = "txn_date,txn_desc,amt,is_credit"


def parse_delimited(uploaded_file: BufferedReader) -> str:
    stream = TextIOWrapper(uploaded_file, encoding='utf-8')
    stream.__next__()
    stream.__next__()
    lines = stream.readlines()
    lines = [str(line).replace(' ', '') for line in lines]
    ret = FILE_HEADER + '\n'
    for line in lines:
        ret += line
    return ret


def parse_cc_csv(uploaded_file: BufferedReader) -> str:
    stream = TextIOWrapper(uploaded_file, encoding='utf-8')

    found_start_point = False
    lines = [CC_FILE_HEADER]

    while not found_start_point:
        line = stream.readline()
        if line.startswith("Transaction type~|~"):
            found_start_point = True

    for line in stream:
        if line == '\n':
            break
        line = line.replace("~|~", '~').strip()
        line = line.split('~')
        line.pop(0)
        line.pop(0)
        line[1] = "\"" + line[1].strip() + "\""
        line[2] = line[2].replace(',', '')
        line[3] = 'N' if line[3] == '' else "Y"
        line.pop(4)
        line = ",".join(line)
        lines.append(line)
    return '\n'.join(lines)


if __name__ == '__main__':
    with open('Examples/HDFC_CC.csv', 'rb') as csvfile:
        with open('Examples/Test.csv', 'w') as f:
            f.writelines(parse_cc_csv(csvfile))
