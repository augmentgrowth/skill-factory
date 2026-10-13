# Expected versus observed

Expected: `writes_to: []` and `tools: [get_page, query, graph, backlinks]` are valid YAML sequences; no A1 invalid-YAML fix should be emitted for them. A4 portability can be assessed separately without changing list types.

Observed: the linter reports each line as an A1 fix and recommends a quoted/block scalar, which changes the field type.

Verification: PyYAML safe_load parsed the original frontmatter successfully and returned a list for tools. This is a linter false positive, not an environment failure. No factory code was changed.
