import copy
import collections
import itertools
try:
    import pyodide.http
    import urllib.parse
    async def fetch_json(url, opts):
        flat_args = []
        for k, vs in opts.items():
            flat_args.extend((k, v) for v in (vs if isinstance(vs, list) else [vs]))
        response = await pyodide.http.pyfetch("%s?%s" % (
            url,
            urllib.parse.urlencode(flat_args),
        ))
        response.raise_for_status()
        return await response.json()
except ImportError:
    import requests
    async def fetch_json(url, opts):
        response = requests.get(url, params=opts)
        response.raise_for_status()
        return response.json()
import re
import warnings

import flexiconc

from . import algo_html
from . import data_util
from . import errors
from . import path_util
from . import tree_html

class FlexiClic():
    def __init__(self, api_root="", install_package_fn=None, available_spacy_models=[]):
        """
        Create a flexiconc<->CLiC adapter

        - api_root: Prefix for API calls, e.g. "https://api.clic-project.org"
        """
        self._api_root = api_root
        self._source_opts = {}
        self._source_annotations = {}
        self._clic_meta = {}
        self._install_package_fn = install_package_fn or None
        self._available_spacy_models = available_spacy_models

    def _flexiconc_concordance(self, data=None):
        if data is not None:
            self._flexiconc = flexiconc.Concordance()
            self._flexiconc.load(**data)
        elif getattr(self, "_flexiconc", None) is None:
            self._flexiconc = flexiconc.Concordance()
        return self._flexiconc

    def _available_algorithms(self, data=None):
        concordance = self._flexiconc_concordance()
        out = concordance.available_algorithms
        # Override Annotate with Sentence Transformers to become server-side
        out['Annotate with Sentence Transformers']["requires"] = []
        out['Annotate with Sentence Transformers']["server_side_prefix"] = "st_"
        out['Annotate with Sentence Transformers']["args_schema"]["properties"] = {
            "model_name": {
                "type": "string",
                "description": "The name of the pretrained Sentence Transformer model.",
                "enum": ["all-MiniLM-L6-v2"],
                "default": "all-MiniLM-L6-v2"
            },
        }
        return out

    async def _follow_path(self, opts=None, annotations=None, path=[], speculative=False):
        """
        Follow path of algorithms, return Node at end

        - opts: dict of arguments to /api/concordance (if not supplied, assume unchanged)
        - annotations: List of annotation algorithms to apply (if not supplied, assume unchanged)
        - path: List of unsorted algorithms to apply
        - speculative: If True, will not continue if we need to regenerate the tree (i.e. query CLiC+annotate)
        """
        concordance = self._flexiconc_concordance()

        if opts is not None and annotations is not None and (self._source_opts != opts or self._source_annotations != annotations):
            self._source_opts = copy.deepcopy(opts)
            self._source_annotations = copy.deepcopy(annotations)
            try:
                if speculative:
                    raise errors.UserConfirmError()

                opts, annotations, annotations_requires = path_util.normalize_source(opts, annotations, self._available_algorithms())

                # Try installing all required packages
                for pkg in annotations_requires:
                    pkg = re.sub(r'[<=>].*$', '', pkg).strip()
                    if self._install_package_fn:
                        await self._install_package_fn(pkg)

                # Fetch query from CLiC server
                data = await fetch_json("%s/api/concordance" % (self._api_root), opts)
                if data.get("error", None):
                    raise ValueError(data["error"].get("message", data["error"]))
                self._clic_meta = {k:data[k] for k in opts.get('metadata', []) + ['version']}

                # Re-create concordance object, add any required annotations
                concordance = self._flexiconc_concordance(data_util.clic_to_flexiconc(
                    data=data.get('data', []),
                    annotation_lines=data.get('annotation_lines', {}),
                ))
                for a in annotations:  # NB: Assume first entry is annotations
                    concordance.add_annotation(
                        (a["algorithm_name"], a["args"]),
                    )
            except:
                # Clear previous attempts so we try again next time
                self._flexiconc = None
                self._source_opts = {}
                self._source_annotations = {}
                raise

        # Try installing all required packages
        path, path_requires = path_util.normalize(path, self._available_algorithms())
        for pkg in path_requires:
            pkg = re.sub(r'[<=>].*$', '', pkg).strip()
            if self._install_package_fn:
                await self._install_package_fn(pkg)

        node = concordance.root
        for node_spec in path:
            if node_spec["algorithm_type"] == "selection":
                node = node.add_subset_node((node_spec["algorithm_name"], node_spec["args"]))
            elif node_spec["algorithm_type"] == "arrangement":
                node = node.add_arrangement_node(
                    ordering=[(x["algorithm_name"], x["args"]) for x in node_spec["ordering"]],
                    grouping=(node_spec["grouping"]["algorithm_name"], node_spec["grouping"]["args"]) if node_spec["grouping"] else None,
                )
            else:
                # NB: At this point other algorithm_types are filed elsewhere
                raise ValueError("Invalid algorithm_type: %s" % node_spec)

        return self._clic_meta, node

    def algorithms_by_class(self):
        """
        Group algorithms by class

        class is a flexiclic invention, and either "annotation" or "algo"
        """
        out = collections.defaultdict(list)
        for algo_name, algo_metadata in self._available_algorithms().items():
            invalid_algo = False
            for prop_name, prop_desc in algo_metadata['args_schema']["properties"].items():
                # Algorithms that expect object aren't supported by CLiC
                if prop_desc.get('type', 'object') == 'object':
                    invalid_algo = True
                    break
            if invalid_algo:
                continue

            algo_class = "annotation" if algo_metadata["algorithm_type"] == "annotation" else "algo"
            out[algo_class].append(dict(
                name=algo_name,
                label=algo_name,
            ))
        return out

    def algorithm_render_html(self, algo_name, prefix):
        concordance = self._flexiconc_concordance()
        algo_schema = self._available_algorithms()[algo_name]
        # If we have data loaded, get context-sensitive schema
        if concordance.metadata is not None and concordance.tokens is not None:
         algo_schema = algo_schema | concordance.root.schema_for(algo_name)

        # If schema involves a spacy model, rewrite it to include the models we have available
        spacy_model = algo_schema.get("args_schema", {}).get("properties", {}).get("spacy_model", None)
        if spacy_model and len(self._available_spacy_models) > 0:
            spacy_model["enum"] = self._available_spacy_models
            spacy_model["default"] = spacy_model["enum"][0]

        return algo_html.from_schema(algo_schema, prefix)

    def tree_ids(self, node=None):
        if node is None:
            node = self._flexiconc_concordance().root
        return [node.id] + [self.tree_ids(node=c) for c in node.children]

    async def render_tree_html(self, opts, annotations, paths):
        # Deep arguments, so will be proxy objects from Javascript
        if hasattr(opts, "to_py"):
            opts = opts.to_py()
        if hasattr(annotations, "to_py"):
            annotations = annotations.to_py()
        if hasattr(paths, "to_py"):
            paths = paths.to_py()

        # Tidy paths, ensuring all paths are present, collect terminal nodes by node_id
        additional_children = collections.defaultdict(list)
        for path_name, node_id in (await self.tidy_paths(opts=opts, annotations=annotations, paths=paths)).items():
            additional_children[node_id].append(path_name)

        # Generate HTML for each terminal node
        additional_children = {node_id: [
            '<div class="button-group" data-path-name="%s"><button class="%s">%s</button><button aria-label="Delete">🗑</button></div>' % (
                n,
                # NB: Should be in lock-step with getMutablePathNumber()
                "" if re.match(r'^\d+$', n) else "immutable",
                n,
            ) for n in path_names
        ] for node_id, path_names in additional_children.items()}

        concordance = self._flexiconc_concordance()
        return tree_html.from_node(concordance.root, additional_children=additional_children)

    async def tidy_paths(self, opts=None, annotations=None, paths={}):
        """
        Remove any extraneous paths from FlexiConc instance
        Return (path_name):(terminal node id) dict
        """
        def tidy_nodes(node, wanted_ids):
            node.children = tuple(tidy_nodes(c, wanted_ids) for c in node.children if c.id in wanted_ids)
            return node

        # Deep arguments, so will be proxy objects from Javascript
        if hasattr(opts, "to_py"):
            opts = opts.to_py()
        if hasattr(annotations, "to_py"):
            annotations = annotations.to_py()
        if hasattr(paths, "to_py"):
            paths = paths.to_py()

        # Add all wanted nodes to set
        wanted_ids = set()
        terminal_node_ids = {}
        for path_name, path in paths.items():
            try:
                _, node = await self._follow_path(opts=opts, annotations=annotations, path=path)
            except Exception as e:
                # This path is invalid for some reason, ignore it
                warnings.warn("Error whilst tidying paths: %s" % e)
                continue
            terminal_node_ids[path_name] = node.id
            while node is not None:
                wanted_ids.add(node.id)
                node = node.parent

        # Search tree, making sure it only contains what's in that set
        concordance = self._flexiconc_concordance()
        tidy_nodes(concordance.root, wanted_ids)
        return terminal_node_ids

    async def compute_path(self, opts, annotations, path, speculative=False):
        """
        Return concordance line data for a path of algorithms

        - opts: CLiC concordance API options
        - annotations: List of annotation algorithms to apply
        - path: List of other algorithms to apply
        """
        def sorted_line_ids(line_ids):
            if hasattr(node, 'ordering_result') and 'sort_keys' in node.ordering_result:
                # Filter sort_keys to include only line_ids in this partition
                partition_sort_keys = {line_id: node.ordering_result["sort_keys"][line_id] for line_id in line_ids if line_id in node.ordering_result["sort_keys"]}
                # Sort line_ids based on sort_keys
                line_ids = sorted(partition_sort_keys, key=partition_sort_keys.get)
            return line_ids

        def to_clic_context(tokens):
            before = tokens['before_token'].tolist()
            word = tokens['word'].tolist()
            after = tokens['after_token'].tolist()

            out = []
            type_idx = []
            for i, _ in enumerate(word):
                if before[i]:  # i.e. ignore 0-length strings
                    out.append(before[i])
                if word[i]:
                    type_idx.append(len(out))
                    out.append(word[i])
                if after[i]:
                    out.append(after[i])
            out.append(type_idx)
            return out

        # Deep arguments, so will be proxy objects from Javascript
        if hasattr(opts, "to_py"):
            opts = opts.to_py()
        if hasattr(annotations, "to_py"):
            annotations = annotations.to_py()
        if hasattr(path, "to_py"):
            path = path.to_py()

        clic_meta, node = await self._follow_path(opts=opts, annotations=annotations, path=path, speculative=speculative)
        view = node.view()

        # Pull concordance DataFrames back out of FlexiConc
        concordance = self._flexiconc_concordance()
        tokens = concordance.tokens
        metadata = concordance.metadata

        if "grouping" in view:
            partition_line_ids = {
                p["label"]: p["line_ids"]
                for p in view["grouping"]
            }
            # We'll be using the query as the node for headers, precalcuate it
            query_as_context = ["|".join([opts["q"]] if isinstance(opts["q"], str) else opts["q"]), []]
        else:
            partition_line_ids = {
                "": view["ordering"],
            }

        if "global_info" in view:
            clic_meta["global_info"] = view["global_info"]

        # Re-organise token_spans by line_id
        token_spans = {}
        for t in view.get("token_spans", []):
            if t["line_id"] not in token_spans:
                token_spans[t["line_id"]] = [t]
            else:
                token_spans[t["line_id"]].append(t)
        line_info = view.get("line_info", {})

        yield clic_meta  # Return clic metadata to client first

        for partition_id, (partition_label, line_ids) in enumerate(partition_line_ids.items()):
            if partition_label != "":
                # Output header row for partition
                yield (
                    ["Partition", []],
                    query_as_context,
                    [partition_label, []],
                    [ "", "", "" ],  # Book/start/end
                    [ "", "", "" ],  # Chap/Par/Sent
                    partition_id,
                    "",  # line_id
                    { "rowcount": len(line_ids) },
                )
            for line_id in line_ids:
                # Borrowed from html_visualizer:_generate_lines_html
                # Get tokens for this line
                line_tokens = tokens[tokens['line_id'] == line_id]

                # Sort tokens by offset and id_in_line to preserve order
                line_tokens = line_tokens.sort_values(by=['offset', 'id_in_line'])
                line_meta = metadata[metadata['line_id'] == line_id].to_dict('records')[0]

                # If we have a token_span, convert it into an array of matches offsets using line IDs (see renderTokenArray)
                if line_id in token_spans:
                    match_range = []
                    for t in token_spans[line_id]:
                        match_range.extend(line_tokens[line_tokens['id_in_line'].between(
                            t["start_id_in_line"],
                            t["end_id_in_line"],
                        )]['offset'].values)
                    matches = [
                        [int(abs(x)) for x in match_range if x < 0],
                        [1] if 0 in match_range else [],
                        [int(x) for x in match_range if x > 0],
                    ]
                else:
                    matches = None

                # Create array entry to be digested in page_flexiconc.js:table_opts.non_tag_columns
                yield (
                    to_clic_context(line_tokens[line_tokens['offset'] < 0]),
                    to_clic_context(line_tokens[line_tokens['offset'] == 0]),
                    to_clic_context(line_tokens[line_tokens['offset'] > 0]),
                    [
                        line_meta['text_id'],  # Book
                        line_meta['cpos_start'],  # Start position
                        line_meta['cpos_end'],  # End position
                    ],
                    [
                        line_meta['chapter'],  # Chapter
                        line_meta['paragraph'],  # Paragraph
                        line_meta['sentence'],  # Sentence
                    ],
                    partition_id,
                    line_id,
                    line_info.get(line_id, {}) | dict(matches=matches),
                )
