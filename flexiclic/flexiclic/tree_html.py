import html
import string


def _algo_to_html(a, algo_type):
    return string.Template("""
<li class="${type}"><h4>${name}</h4>${args}</li>
    """.strip()).substitute(
        type=a.get("algorithm_type", algo_type),
        name=html.escape(a["algorithm_name"]),
        args=html.escape(str(a["args"])),
    )


def _node_to_html(node):
    algos_html = ""
    for algo_type, algos in getattr(node, "algorithms", {}).items():
        if algos is None:
            continue
        if type(algos) != list:
            algos = [algos]
        if len(algos) == 0:
            continue
        algos_html += '<ul class="%s">%s</ul>' % (
            algo_type,
            "\n".join(_algo_to_html(a, algo_type) for a in algos),
        )

    if node.parent is None:
        return '<div class="node root"></div>'
    return string.Template("""
<div class="node ${type}">
  <header>${type}</header>
  ${algos_html}
</div>
    """.strip()).substitute(
        type=html.escape(node.node_type),
        algos_html=algos_html,
        #algos_html=html_list(list(_algo_to_html(a) for a in getattr(node, "algorithms", []))),
    )


def from_node(node, additional_children={}, root=True):
    """
    Given a FlexiConc (node), return an HTML list structure representing the FlexiConc tree below

    - node: The FlexiConc root node
    - root: Should remain True
    """
    has_children = bool(node.children or len(additional_children.get(node.id, [])) > 0)
    yield '%s<li class="tree">%s%s' % (
        '<ul class="tree">' if root else '',
        _node_to_html(node),
        '<ul class="tree">' if has_children else '',
    )
    for subnode in node.children:
        yield from from_node(subnode, additional_children=additional_children, root=False)
    for subhtml in additional_children.get(node.id, []):
        yield '<li class="tree">%s</li>' % subhtml
    yield '%s</li>%s' % (
        '</ul>' if has_children else '',
        '</ul>' if root else '',
    )
