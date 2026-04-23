import csv


def read_openrocket_csv_lines(csv_path):
    with open(csv_path, 'r', encoding='latin-1') as handle:
        return handle.readlines()


def detect_header_and_data_start(lines):
    header = None
    data_start = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('#') and ',' in stripped:
            header = stripped.lstrip('#').strip().split(',')
        elif not stripped.startswith('#'):
            data_start = idx
            break
    return header, data_start


def find_header_index(header, name):
    for idx, col_name in enumerate(header):
        if name in col_name:
            return idx
    raise ValueError(f"'{name}' not found in CSV header")


def iter_csv_rows(lines, data_start):
    return csv.reader(lines[data_start:])
