import html
import string


def from_schema(algo, index=0):
    """
    Convert an algorithm schema into a HTML form snippet

    - algo: The algorithm schema
    - index: The index of this algorithm in it's overall list 
    """
    args_schema = algo['args_schema']
    if args_schema['type'] != "object":
        raise ValueError("Unknown args schema type %s" %  args_schema['type'])

    yield "<legend>%s</legend>" % html.escape(algo['full_name'])
    yield html_prop_hidden(
        name="algo_name[%s][]" % (algo["algorithm_type"]),
        value=algo['full_name'],
    )

    for prop_name, prop_desc in args_schema["properties"].items():
        input_name = "algo[%s][%d][%s]" % (algo["algorithm_type"], index, prop_name)
        yield html_prop(input_name, prop_desc)


def html_prop(input_name, prop_desc):
    """
    Generate HTML for an individual property

    - input_name: The name for the HTML input
    - prop_desc: The FlexiConc property schema
    """
    # Assume any prop_desc with missing type are objects
    if prop_desc.get('type', 'object') == 'object':
        return '<pre style="border: 1px solid red">Object type is too loose: %s</pre>' % prop_desc

    if 'enum' in prop_desc:
        if prop_desc['type'] != 'string':
            import pdb ; pdb.set_trace()
        return html_prop_select(
            input_type="text",
            name=input_name,
            label=prop_desc["description"],
            options=[dict(
                value=x,
                label=x,
                selected=(x == prop_desc.get("default", "")),
            ) for x in prop_desc['enum']],
        )

    if prop_desc['type'] == 'string' or prop_desc['type'] == ['string']:
        return html_prop_inputbox(
            input_type="text",
            name=input_name,
            label=prop_desc["description"],
            value=prop_desc.get("default") or None,
        )

    if prop_desc['type'] == 'boolean':
        return html_prop_checkbox(
            input_type="number",
            name=input_name,
            label=prop_desc["description"],
            value=prop_desc.get("default") or False,
        )

    if prop_desc['type'] == 'integer' or prop_desc['type'] == ['integer'] or prop_desc['type'] == ['integer', 'number'] or prop_desc['type'] == ['number', 'integer']:
        return html_prop_inputbox(
            input_type="number",
            name=input_name,
            label=prop_desc["description"],
            value=prop_desc.get("default") or None,
            step=1,  # TODO: Need to apply step when type is number, but to what?
        )

    if prop_desc['type'] == 'array' or prop_desc['type'] == ['array']:
        return '<pre style="border: 1px solid red">type: array not supported: %s</pre>' % prop_desc

    raise ValueError('Unknown type: %s</pre>' % prop_desc)


def html_prop_inputbox(input_type, name, label, **props):
    """
    Generate an HTML-input based control
    """
    return string.Template("""
<label for="ctlb-flexiconc-${name}">${label}</label>
<input type="${input_type}" name="${name}" id="ctlb-flexiconc-${name}" class="form-control" ${props}>
    """.strip()).substitute(
        name=name,
        input_type=input_type,
        label=html.escape(label),
        props=" ".join('%s="%s"' % (k, html.escape(str(v), quote=True)) for k, v in props.items() if v is not None)
    )


def html_prop_hidden(name, **props):
    """
    Generate a hidden input control
    """
    return string.Template("""
<input type="${input_type}" name="${name}" ${props}>
    """.strip()).substitute(
        name=name,
        input_type="hidden",
        props=" ".join('%s="%s"' % (k, html.escape(str(v), quote=True)) for k, v in props.items() if v is not None)
    )


def html_prop_checkbox(input_type, name, label, value, **props):
    """
    Generate an HTML-input based control
    """
    return string.Template("""
<div class="checkbox"><label>
    <input type="checkbox" name="${name}" ${props} ${checked}>
    <span>${label}</span>
 </label></div>
    """.strip()).substitute(
        name=name,
        type=input_type,
        label=html.escape(label),
        checked=" checked" if value else "",
        props=" ".join('%s="%s"' % (k, html.escape(str(v), quote=True)) for k, v in props.items() if v is not None)
    )


def html_prop_select(input_type, name, label, options, **props):
    """
    Generate an HTML-select based control
    """
    def html_option(value, label, selected):
        return """<option value="%s" %s>%s</option>""" % (
            html.escape(value, quote=True),
            " selected" if selected else "",
            html.escape(label),
        )

    return string.Template("""
<label for="ctlb-flexiconc-${name}">${label}</label>
<select name="${name}" id="ctlb-flexiconc-${name}" class="chosen-select" ${props}>${options}</select>
    """.strip()).substitute(
        name=name,
        type=input_type,
        label=html.escape(label),
        options=" ".join(html_option(**o) for o in options),
        props=" ".join('%s="%s"' % (k, html.escape(str(v), quote=True)) for k, v in props.items() if v is not None)
    )
