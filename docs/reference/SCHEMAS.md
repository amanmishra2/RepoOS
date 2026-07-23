# Schema reference

RepoOS uses JSON Schema Draft 2020-12 with unknown-field rejection:

- `project-registry.schema.json`
- `project-manifest.schema.json`
- `observation.schema.json`
- `candidate-pattern.schema.json`
- `adoption-record.schema.json`
- `update-plan.schema.json`

Validate a document:

```bash
repoos validate path/to/document.yaml --schema project-manifest
```

Validate all RepoOS surfaces:

```bash
repoos --format json validate --all
```

Schema validity, valid examples, invalid examples, traversal rejection, and current repository records are covered by `tests/schema/`.
