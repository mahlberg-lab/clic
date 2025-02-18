from .errors import UserError

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
            if arg_spec["type"] == "boolean" or arg_spec["type"] == ["boolean"]:
                val = bool(val)  # NB: Assume missing values are also "False"
            elif arg_spec["type"] == "integer" or arg_spec["type"] == ["integer"]:
                val = None if val is None else int(val)
            algo["args"][arg_k] = val

        # File appropriately, annotations are separate, sort/group get combined into an arrangement pseudo-algorithm
        if algo["algorithm_type"] == "annotation":
            algo["column_name"] = algo["algorithm_name"]
            annotations.append(algo)
        elif algo["algorithm_type"] in set(("sorting", "grouping")):
            if len(out) == 0 or out[-1]["algorithm_type"] != "arrangement":
                # Start new arrangement node
                out.append(dict(
                    algorithm_type="arrangement",
                    ordering=[],
                    grouping=None
                ))
            if algo["algorithm_type"] == "sorting":
                out[-1]["ordering"].append(algo)
            else:  # i.e. grouping
                if out[-1]["grouping"] is not None:
                    raise ValueError("Cannot have multiple grouping nodes in a row")
                out[-1]["grouping"].append(algo)
        elif algo["algorithm_type"] == "selection":
            out.append(algo)
        else:
            raise ValueError("Unknown algorithm_type: %s" % algo["algorithm_type"])

    return out, annotations
