"""Present one real bounded UTF8 input segment; never emit a reading receipt."""
import argparse
from pathlib import Path
from transport_common import allowed_inputs, check, presentation_payload

def present(assignment_path, path, start, end):
    _, allowed = allowed_inputs(assignment_path)
    path = str(Path(path).resolve())
    if path not in allowed:
        raise ValueError("Path is outside this batch's allowed research inputs")
    b = allowed[path]
    check(b)
    text = Path(path).read_bytes().decode("utf-8")
    if type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text) or end - start > 2500:
        raise ValueError("Invalid/oversized actual presentation interval")
    return presentation_payload(b, text, start, end)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assignment", required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--start", required=True, type=int)
    p.add_argument("--end", required=True, type=int)
    a = p.parse_args()
    print(present(a.assignment, a.path, a.start, a.end), end="")
