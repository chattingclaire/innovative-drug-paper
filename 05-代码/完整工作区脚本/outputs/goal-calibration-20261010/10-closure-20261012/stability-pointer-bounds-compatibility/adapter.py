"""Candidate-only in-memory adapter; no receiving, dispatch, locking or file writes."""
import functools
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def check(expected):
    if binding(expected["path"]) != expected:
        raise ValueError("Changed bound input: " + expected["path"])


def manifest():
    return json.loads((HERE / "manifest.json").read_bytes())


def _list_bounds_failure(packet, pointer):
    """Classify only exact JSON containers and the original canonical index syntax."""
    if type(pointer) is not str or not pointer.startswith("/"):
        return None
    current = packet
    for encoded in pointer[1:].split("/"):
        part = encoded.replace("~1", "/").replace("~0", "~")
        if type(current) is list:
            if not part.isdigit() or str(int(part)) != part:
                return None
            index = int(part)
            if index >= len(current):
                return {"index": index, "length": len(current)}
            current = current[index]
        elif type(current) is dict and part in current:
            current = current[part]
        else:
            return None
    return None


def wrap_pointer_value(original):
    """Keep the original result/errors except genuine built-in list bounds errors."""
    @functools.wraps(original)
    def wrapped(packet, pointer):
        try:
            return original(packet, pointer)
        except IndexError as error:
            bounds = _list_bounds_failure(packet, pointer)
            if bounds is None:
                raise
            raise ValueError(
                "Packet JSON pointer array index out of range: "
                f"{pointer}; index={bounds['index']}, length={bounds['length']}"
            ) from error
    return wrapped


def patch_validator_module(module):
    """Patch one freshly loaded original module in memory; originals remain bound."""
    expected = manifest()["original_validator"]
    check(expected)
    if str(Path(module.__file__).resolve()) != expected["path"]:
        raise ValueError("Only the bound original validator may be adapted")
    function = module.pointer_value
    if function.__code__.co_filename != expected["path"] or function.__name__ != "pointer_value":
        raise ValueError("Expected the original unwrapped pointer_value")
    module.pointer_value = wrap_pointer_value(function)
    return module


def load_readonly_validator():
    """Load a private module for pure verify calls; never invoke receive/run."""
    expected = manifest()["original_validator"]
    check(expected)
    spec = importlib.util.spec_from_file_location("readonly_pointer_bounds_validator", expected["path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return patch_validator_module(module)


def wrap_receiver_module_loader(original_loader):
    """Candidate hook for a separately authorized, terminal-only runtime integration.

    A future entry may assign this return value to the original receiver.module.
    This factory neither imports the receiver nor invokes receiving or dispatch.
    Every original load/check still runs. Only the exact bound validator used by
    verify_capture gets its pointer_value wrapped; all other loads pass through.
    """
    document = manifest()
    for key in ("original_validator", "original_receiver", "original_transport_common"):
        check(document[key])
    @functools.wraps(original_loader)
    def load(expected, name):
        module = original_loader(expected, name)
        if name == "unchanged_production_validator_capture" and expected == document["original_validator"]:
            return patch_validator_module(module)
        return module
    return load
