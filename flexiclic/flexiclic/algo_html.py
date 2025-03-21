import json
import html
import string


def from_schema(algo, prefix="algo"):
    """
    Convert an algorithm schema into a HTML form snippet

    - algo: The algorithm schema
    - prefix: The prefix for all form field names
    """
    algo_class = "annotation" if algo["algorithm_type"] == "annotation" else "algo"
    args_schema = algo['args_schema']
    args_required = set(args_schema.get("required", ()))
    if args_schema['type'] != "object":
        raise ValueError("Unknown args schema type %s" %  args_schema['type'])

    yield '<button type="button" class="control" aria-label="Close"><span aria-hidden="true">&times;</span></button>'

    yield "<legend>%s</legend>" % html.escape(algo['full_name'])
    yield html_prop_hidden(
        name="%s[%s]" % (prefix, "algorithm_name"),
        value=algo['full_name'],
    )

    for prop_name, prop_desc in args_schema["properties"].items():
        yield html_prop(
            "%s[%s]" % (prefix, prop_name),
            prop_desc,
            required=prop_name in args_required,
        )
        if 'x-eval-error' in prop_desc:
            yield '<pre style="border: 1px solid red">%s</pre>' % html.escape(prop_desc['x-eval-error'])

    if algo_class == "algo":
        # Fake button so they still work if the fieldset is disabled: https://stackoverflow.com/a/55155649
        yield '<div class="control fork" aria-role="button" aria-label="Fork"><span aria-hidden="true"><img src="/icons/fork.svg" width="13" height="18" alt="Fork from this point" /></span></div>'


def html_prop(input_name, prop_desc, required=False):
    """
    Generate HTML for an individual property

    - input_name: The name for the HTML input
    - prop_desc: The FlexiConc property schema
    - required: Property is required?
    """
    # Assume any prop_desc with missing type are objects
    prop_type = prop_desc.get('type', 'object')
    prop_type = set((prop_type,)) if isinstance(prop_type, str) else set(prop_type)

    if prop_type == 'object':
        return '<pre style="border: 1px solid red">Object type is too loose: %s</pre>' % prop_desc

    if input_name.endswith('[line_ids]'):
        return html_prop_lineid_picker(
            name=input_name,
            label=prop_desc["description"],
            values=prop_desc.get("default", []),
            fc_select_type="line_id",
            required=required,
        )

    if input_name.endswith('[groups]'):
        return html_prop_lineid_picker(
            name=input_name,
            label=prop_desc["description"],
            values=prop_desc.get("default", []),
            fc_select_type="partition_label",
            required=required,
        )

    if 'enum' in prop_desc:
        if prop_type != set(("string",)):
            return '<pre style="border: 1px solid red">Non-string enum: %s</pre>' % prop_desc
        return html_prop_select(
            name=input_name,
            label=prop_desc["description"],
            options=[dict(
                value=x,
                label=x,
                selected=(x == prop_desc.get("default", "")),
            ) for x in prop_desc['enum']],
            required=required,
        )

    if prop_type == set(("boolean",)):
        return html_prop_checkbox(
            input_type="number",
            name=input_name,
            label=prop_desc["description"],
            value=prop_desc.get("default") or False,
        )

    if prop_type == set(("integer",)) or prop_type == set(("number",)) or prop_type == set(("integer", "number")):
        return html_prop_inputbox(
            input_type="number",
            name=input_name,
            label=prop_desc["description"],
            value=prop_desc.get("default") or None,
            step=prop_desc.get("step", 1 if "integer" in prop_type else None),
            min=prop_desc.get("minimum"),
            max=prop_desc.get("maximum"),
            required=required,
        )

    if "array" in prop_type:
        enum = [
            dict(value=x, label=x, selected=False)
            for x in prop_desc.get("items", {}).get("enum", [])
        ]
        return html_prop_select(
            name=input_name,
            label=prop_desc["description"],
            options=enum or [],
            classes=["allow-add-items" if len(enum) == 0 else ""],
            multiple="multiple",
            required=required,
        )

    if "string" in prop_type:
        return html_prop_inputbox(
            input_type="text",
            name=input_name,
            label=prop_desc["description"],
            value=prop_desc.get("default") or None,
            required=required,
        )

    raise ValueError('Unknown type: %s</pre>' % prop_desc)


def html_prop_inputbox(input_type, name, label, required=False, **props):
    """
    Generate an HTML-input based control
    """
    return string.Template("""
<label for="ctlb-flexiconc-${name}">${required_html}${label}</label>
<input type="${input_type}" name="${name}" id="ctlb-flexiconc-${name}" class="form-control" ${props}>
    """.strip()).substitute(
        name=name,
        input_type=input_type,
        label=html.escape(label),
        props=" ".join('%s="%s"' % (k, html.escape(str(v), quote=True)) for k, v in props.items() if v is not None),
        required_html='<span style="color: red" title="This property is required">*</span> ' if required else '',
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


def html_prop_select(name, label, options, classes = [], required=False, **props):
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
<label for="ctlb-flexiconc-${name}">${required_html}${label}</label>
<select name="${name}" id="ctlb-flexiconc-${name}" class="tomselect ${klass}" ${props}>${options}</select>
    """.strip()).substitute(
        name=name,
        label=html.escape(label),
        options=" ".join(html_option(**o) for o in options),
        klass=" ".join(classes),
        props=" ".join('%s="%s"' % (k, html.escape(str(v), quote=True)) for k, v in props.items() if v is not None),
        required_html='<span style="color: red" title="This property is required">*</span> ' if required else '',
    )


def html_prop_lineid_picker(name, label, values=[], fc_select_type="line_id", required=False, **props):
    """
    Generate HTML for a lineid picker
    """
    return string.Template("""
<label for="ctlb-flexiconc-${name}">${required_html}${label}</label>
<div class="button-group">
<input type="text" name="${name}" value="${value_concat}" class="lineid-picker" data-fc-select-type="${fc_select_type}" readonly="readonly" ${props}>
</div>
    """.strip()).substitute(
        name=name,
        label=html.escape(label),
        fc_select_type=fc_select_type,
        required_html='<span style="color: red" title="This property is required">*</span> ' if required else '',
        value_concat=json.dumps(values),
        props=" ".join('%s="%s"' % (k, html.escape(str(v), quote=True)) for k, v in props.items() if v is not None),
    )
