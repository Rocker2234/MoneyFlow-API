import csv
import io
from csv import DictReader

from .parsers import HDFC
from config.groupers import custom

PARSER_MAPPING = {
    'HDFC_D': HDFC.parse_delimited
}


def get_reader(file, parser_name: str) -> DictReader:
    data = PARSER_MAPPING[parser_name](file)
    reader = csv.DictReader(io.StringIO(data))
    return reader


def get_group(txn_desc: str, grouper: str) -> str:
    if grouper in (None, '', '<skip>'):
        return ''
    elif grouper == 'G_HDFC_X':
        return custom.hdfc_grouper(txn_desc)
    return ''
