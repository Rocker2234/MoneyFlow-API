import csv
import io
from csv import DictReader

from jinja2.sandbox import SandboxedEnvironment

from .parsers import HDFC

PARSER_MAPPING = {
    'HDFC_D': HDFC.parse_delimited
}


def get_reader(file, parser_name: str) -> DictReader:
    data = PARSER_MAPPING[parser_name](file)
    reader = csv.DictReader(io.StringIO(data))
    return reader


def get_group(grouper_env: SandboxedEnvironment, txn_desc: str, grouper: str) -> str:
    if grouper in (None, '', '<skip>'):
        return ''
    template = grouper_env.get_template('G_' + grouper + '.j2')
    return template.render(txn_desc=txn_desc).strip()
