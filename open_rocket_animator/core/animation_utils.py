import math


def get_anim_data(id_data):
    return getattr(id_data, "animation_data", None)


def get_action_and_slot(id_data):
    anim_data = get_anim_data(id_data)
    if not anim_data:
        return None, None
    action = getattr(anim_data, "action", None)
    slot = getattr(anim_data, "action_slot", None)
    if not action or not slot:
        return action, slot
    return action, slot


def _get_channelbag_for_slot(strip, slot):
    if strip is None or slot is None:
        return None

    for method_name in ("channelbag", "channelbag_for_slot"):
        method = getattr(strip, method_name, None)
        if callable(method):
            try:
                return method(slot)
            except Exception:
                pass

    channelbags = getattr(strip, "channelbags", None)
    if channelbags is not None:
        key = getattr(slot, "identifier", None) or getattr(slot, "name", None)
        getter = getattr(channelbags, "get", None)
        if callable(getter) and key is not None:
            return getter(key)

    return None


def iter_slot_fcurves(id_data):
    action, slot = get_action_and_slot(id_data)
    if not action or not slot:
        return

    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            strip_type = getattr(strip, "type", "")
            if strip_type not in {"KEYFRAME", "KEYFRAME_STRIP"}:
                continue
            channelbag = _get_channelbag_for_slot(strip, slot)
            if not channelbag:
                continue
            for fcurve in getattr(channelbag, "fcurves", []):
                yield fcurve


def find_or_create_slot_fcurve(id_data, data_path, index):
    action, slot = get_action_and_slot(id_data)
    if not action or not slot:
        return None

    for fcurve in iter_slot_fcurves(id_data):
        if fcurve.data_path == data_path and fcurve.array_index == index:
            return fcurve

    ensure_func = getattr(action, "fcurve_ensure_for_datablock", None)
    if callable(ensure_func):
        try:
            return ensure_func(datablock=id_data, data_path=data_path, index=index)
        except TypeError:
            try:
                return ensure_func(id_data, data_path, index)
            except Exception:
                return None
        except Exception:
            return None
    return None


def compute_attitude_euler(vertical_deg, lateral_deg, roll_rad=0.0):
    # Conservative mapping for this add-on: zenith -> X tilt, azimuth -> Z heading, roll -> Y axis.
    vertical_rad = math.radians(vertical_deg)
    lateral_rad = math.radians(lateral_deg)
    return (vertical_rad, roll_rad, lateral_rad)
