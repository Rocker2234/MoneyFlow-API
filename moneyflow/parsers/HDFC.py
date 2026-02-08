from io import BufferedReader, TextIOWrapper

from . import FILE_HEADER


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
