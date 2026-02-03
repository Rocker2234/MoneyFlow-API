import io

from . import FILE_HEADER


def parse_delimited(file):
    file.__next__()
    file.__next__()
    lines = file.readlines()
    lines = [line.replace(' ', '') for line in lines]
    print(f"Number of transactions: {len(lines)}")
    ret = FILE_HEADER + '\n'
    for line in lines:
        ret += line
    return ret
