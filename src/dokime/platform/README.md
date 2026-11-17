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

## The composition with a patch

`compose_with_patch(base, patch)` applies the patch with `git apply --cached` to an index of the
adapter from the tree of the base, so no working tree and no git directory of the project is
touched. A patch that does not apply is refused with `patch-does-not-apply`, quoting git. Before
applying, the paths that git reads from the patch are checked, and one with a part `.git` in any
case of letters is refused with `patch-touches-git`.

## The ledger store of a file and the system clock

`LedgerFile(path)` implements the port of the ledger store of `core` over one file of the state
directory of the harness: one event per line, each ended by a newline, written in append mode until
every byte of the line is written, and flushed to the storage device before `append` returns, with
its directory when the file is new. It refuses a line with a newline or a carriage return, and
appending after a last line that was cut. A file that does not exist has no lines and is created by
the first append. `SystemClock` implements the port of the clock with the time of the system in UTC.

```python
from dokime.core.ledger import Ledger
from dokime.platform.clock import SystemClock
from dokime.platform.ledger_file import LedgerFile

ledger = Ledger(LedgerFile(state / "ledger.jsonl"), SystemClock())
ledger.record("run.started", {})
```
