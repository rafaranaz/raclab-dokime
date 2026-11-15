# platform

Adapters of the outside world that do not run code of others. It imports only `core`, and only
`interfaces` imports it. This increment has the adapter of the project repository that runs the
`git` command; its requirements are in [platform.md](../../../docs/requirements/platform.md).

## The git adapter

```python
from dokime.platform.git import GitRepository

with GitRepository(project) as repository:  # refuses git older than 2.41, SHA-256, shallow
    repository.git_path, repository.git_version  # the git that every command runs
    history = repository.history(start)
    change = repository.change(commit)  # the paths against its one parent
    tree = repository.compose_with_paths(change.parent, commit, is_test)
    repository.extract(tree, directory)  # an empty directory, filled byte for byte
```

The adapter reads three facts in the project: that it is a repository, the format of its objects
and whether it is a shallow clone. Everything else runs in a bare repository of its own, in a
temporary directory removed on `close()`, which reads the objects of the project as alternates.
The configuration and the attributes of the project and of the person do not reach it, and the
`.git` of the project is not written. A tree with a submodule is refused, and a composition with a
patch is refused until milestone A3.
