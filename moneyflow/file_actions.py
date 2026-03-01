import csv
import io
from csv import DictReader
from io import BufferedReader

from jinja2 import Template

from .parsers import HDFC, ICICI, KTKB, SBI

PARSER_MAPPING = {
    'HDFC_D': HDFC.parse_delimited,
    "HDFC_CC_CSV": HDFC.parse_cc_csv,
    "ICICI_XLS": ICICI.parse_xls,
    'KTKB_XLS': KTKB.parse_xls,
    'SBI_XLSX': SBI.parse_xlsx,
}


def get_reader(file: BufferedReader, parser_name: str, pw: str = None) -> DictReader:
    if pw:
        data = PARSER_MAPPING[parser_name](file, pw)
    else:
        data = PARSER_MAPPING[parser_name](file)
    reader = csv.DictReader(io.StringIO(data))
    return reader


def get_group(template: Template, txn_desc: str) -> str:
    if template is None:
        return ''
    return template.render(txn_desc=txn_desc).strip()
