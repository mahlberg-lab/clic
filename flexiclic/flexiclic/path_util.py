from .errors import UserError

def convert_value(val, target_types, items):
    """
    Convert (val) to one of (target_types)

    - val: Either None (missing value) or string
    - target_types: (list of) acceptible transformations, "string", "integer", "boolean", ..
    - items: Dict of sub-type options, used for arrays
    """
    if target_types is None:
        target_types = ["string"]
    elif isinstance(target_types, str):
        target_types = [target_types]

    for t in target_types:
        try:
            if t == "array":
                if val is None:
                    val = []
                elif not isinstance(val, list):
                    val = [convert_value(v, items.get("type"), {}) for v in [val]]
                else:
                    val = [convert_value(v, items.get("type"), {}) for v in val]
            elif t == "boolean":
                val = bool(val)  # NB: Assume missing is false
            elif t == "string":
                val = None if val is None else str(val)
            elif t == "integer":
                val = None if val is None else int(val)
            elif t == "number":
                val = None if val is None else float(val)
            else:
                raise ValueError("Unknown type %s" % t)
            return val
        except ValueError:
            pass  # Conversion failed, try the next type
    raise UserError("Cannot convert '%s' to %s" % (
        val,
        target_types
    ), "warn")


def normalize(path, available_algorithms):
    annotations = []
    out = []

    for raw_spec in path:
        # Ensure algo is a dict of name/type/expected arguments
        algo_metadata = available_algorithms[raw_spec["algorithm_name"]]
        algo = dict(
            algorithm_name=raw_spec["algorithm_name"],
            algorithm_type=algo_metadata["algorithm_type"],
            args={},
        )
        arg_required = set(algo_metadata["args_schema"]["required"])
        for arg_k, arg_spec in algo_metadata["args_schema"]["properties"].items():
            val = raw_spec.get(arg_k) or arg_spec.get("default")
            if arg_k in arg_required and val is None:
                raise UserError("Argument %s for %s is required" % (arg_k, algo_metadata["full_name"]), "warn")
            val = convert_value(val, arg_spec["type"], items=arg_spec.get('items', {}))
            # Any values of None should be missing from the schema, so we don't trigger validation problems
            if val is not None:
                algo["args"][arg_k] = val

        # File appropriately, annotations are separate, sort/group get combined into an arrangement pseudo-algorithm
        if algo["algorithm_type"] == "annotation":
            algo["column_name"] = algo["algorithm_name"]
            annotations.append(algo)
        elif algo["algorithm_type"] in ("sorting", "ranking", "partitioning", "clustering"):  # NB: clustering is assumed
            if (len(out) == 0 or
                    # Final node isn't an arrangement
                    out[-1]["algorithm_type"] != "arrangement" or
                    # Final node is an arrangement, but already has a partitioning/clustering node
                    (algo["algorithm_type"] in ("partitioning", "clustering") and out[-1]["grouping"] is not None)):
                # Start new arrangement node
                out.append(dict(
                    algorithm_type="arrangement",
                    ordering=[],
                    grouping=None
                ))
            if algo["algorithm_type"] in ("sorting", "ranking"):
                out[-1]["ordering"].append(algo)
            else:  # i.e. grouping
                out[-1]["grouping"] = algo
        elif algo["algorithm_type"] == "selection":
            out.append(algo)
        else:
            raise ValueError("Unknown algorithm_type: %s" % algo)

    return annotations + out
