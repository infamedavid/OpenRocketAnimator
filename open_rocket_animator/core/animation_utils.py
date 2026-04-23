def get_anim_data(id_data):
    return getattr(id_data, "animation_data", None)


def get_action_and_slot(id_data):
    anim_data = get_anim_data(id_data)
    if not anim_data:
        return None, None, None

    action = getattr(anim_data, "action", None)
    slot = getattr(anim_data, "action_slot", None)

    if not action or not slot:
        return anim_data, action, None

    return anim_data, action, slot


def _get_channelbag_for_slot(strip, slot):
    if strip is None or slot is None:
        return None

    for method_name in ("channelbag", "channelbag_for_slot"):
        method = getattr(strip, method_name, None)
        if callable(method):
            try:
                return method(slot)
            except Exception:
                continue

    channelbags = getattr(strip, "channelbags", None)
    if channelbags is not None:
        getter = getattr(channelbags, "get", None)
        if callable(getter):
            key = getattr(slot, "identifier", None)
            if key is None:
                key = getattr(slot, "name", None)
            if key is not None:
                return getter(key)

    return None


def iter_slot_fcurves(id_data):
    _anim_data, action, slot = get_action_and_slot(id_data)
    if not action or not slot:
        return

    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            if getattr(strip, "type", None) not in {"KEYFRAME", 'KEYFRAME_STRIP'}:
                continue
            channelbag = _get_channelbag_for_slot(strip, slot)
            if not channelbag:
                continue
            for fcurve in getattr(channelbag, "fcurves", []):
                yield fcurve


def ensure_fcurve_for_datablock(id_data, data_path, index=0, group_name=""):
    _anim_data, action, _slot = get_action_and_slot(id_data)
    if not action:
        return None

    ensure_func = getattr(action, "fcurve_ensure_for_datablock", None)
    if callable(ensure_func):
        kwargs = {
            "datablock": id_data,
            "data_path": data_path,
            "index": index,
        }
        if group_name:
            kwargs["group"] = group_name
        try:
            return ensure_func(**kwargs)
        except TypeError:
            try:
                return ensure_func(id_data, data_path, index)
            except Exception:
                return None
        except Exception:
            return None

    return None
