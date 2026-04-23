import csv
import math


def read_openrocket_csv_lines(csv_path):
    with open(csv_path, 'r', encoding='latin-1') as handle:
        return handle.readlines()


def detect_header_and_data_start(lines):
    header = None
    data_start = None

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#') and ',' in stripped:
            header = [item.strip() for item in stripped.lstrip('#').strip().split(',')]
            continue
        if stripped.startswith('#'):
            continue

        if header is not None:
            data_start = idx
            break

    return header, data_start


def find_header_index(header, substring):
    lowered = substring.lower()
    for idx, col_name in enumerate(header):
        if lowered in col_name.lower():
            return idx
    return -1


def safe_float(value):
    try:
        number = float(value)
        if math.isnan(number):
            return None
        return number
    except Exception:
        return None


def iter_csv_rows(lines, data_start):
    return csv.reader(lines[data_start:])


def find_orientation_indices(header):
    return {
        "vertical": find_header_index(header, "Vertical orientation (zenith)"),
        "lateral": find_header_index(header, "Lateral orientation (azimuth)"),
        "roll_rate": find_header_index(header, "Roll rate"),
    }
