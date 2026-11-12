# ADR-0042 · A port of the project repository composes the trees that are built

**Status:** proposed

## Context

The self-check of a pack ([ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.md))
asks git three things about the verified project: which commits it has, which paths each one
changed, and the files of a commit. No port of the [module map](../architecture/02-modules.md#ports)
answers them.

The port of the verification runtime says "build an image from a pack and a commit". What is
built is often not a commit. The parent side of a candidate is the code of the parent with the
tests of the commit. In milestone A3 it is the base commit with the patch applied
([ADR-0016](0016-verification-in-a-container-on-base-plus-patch.md)). The subject of the evidence
is the digest of the resulting tree, not a commit
([ADR-0023](0023-evidence-is-an-attestation-bound-to-the-tree.md)), so whatever is built has to be
known by that digest.

## Decision

- **A port of its own.** `core` defines a port of the project repository. Its adapter lives in
  `platform` and runs `git`. It lists commits, gives the parent and the changed paths of a commit,
  composes trees and extracts a tree to a directory.
- **The port composes; the domain decides what.** The port offers two compositions: the tree of a
  commit with a set of paths taken from another commit, and the tree of a commit with a patch
  applied. Which paths are tests is decided by the module that holds the rule (`packs` for the
  self-check), not by the adapter.
- **A tree is named by its git tree digest.** Each composition returns that digest. The directory
  given to the runtime is extracted from the digest, byte for byte: without the attributes of the
  project (`export-ignore`, `export-subst`, `eol`, filters) and without the git configuration of the
  person (`core.autocrlf`). The directory holds no `.git`.
- **The project repository is only read.** The objects a composition writes go to a directory of
  the harness that uses the objects of the project as alternates. Nothing is written in the `.git`
  of the project.
- **The runtime knows nothing of git.** The port of the verification runtime receives a Dockerfile,
  a directory and the digest of the tree it holds. It builds, runs and records that digest.

The order in which commits are listed is not decided here.

## Basis

Verified on 2026-11-12 with git 2.47.3, docker 29.9.3, podman 5.4.2 and buildah 1.39.3, on local
clones of the corpus, the originals untouched.

- The three engines build from a directory and a Dockerfile outside it (`build -f`). The
  self-check of cachetools gave the same seven witnesses out of ten on the three engines, with the
  twenty JUnit reports identical test by test.
- A tree is composed without touching the files of the project, with a throwaway index. The parent
  of `e963102` with its tests gave the tree `d5ff931…`, whose extraction equals the directory the
  self-check used. The base with the full diff of `e963102` gave exactly the tree of `e963102`.

  ```sh
  export GIT_INDEX_FILE=$TMP/index
  git read-tree "$commit^"
  git ls-files -- tests/ | git update-index --force-remove --stdin
  git ls-tree -r "$commit" -- tests/ | git update-index --index-info
  git write-tree                                  # parent side
  git read-tree "$base" && git apply --cached patch.diff && git write-tree   # base plus patch
  ```

- `git archive` does not give the tree. On a commit that marks a test `export-ignore`, a file
  `export-subst` and `*.py` as `eol=crlf`, the archive of the tree left the test out and its digest
  differed. The archive of the commit also replaced `$Format:%H$`. `checkout-index` wrote CRLF in 21
  files. Reading the attributes from the empty tree and forcing the end of line gave a directory
  equal byte for byte to the blobs. `core.autocrlf=true` in the global configuration changed 45
  files until the configuration was isolated.

  ```sh
  export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1 GIT_INDEX_FILE=$TMP/index
  empty=4b825dc642cb6eb9a060e54bf8d69288fbee4904
  git -c core.autocrlf=false -c core.eol=lf --attr-source=$empty read-tree "$tree"
  git -c core.autocrlf=false -c core.eol=lf --attr-source=$empty checkout-index -a --prefix="$dir/"
  ```

- On a fresh clone, composing the trees of `c8b4ee2` wrote two objects. With the variables below
  they went to the directory of the harness, the `.git` of the project stayed equal byte for byte
  and did not know the new tree. The same composition without them changed the `.git`.

  ```sh
  export GIT_OBJECT_DIRECTORY=$TMP/objects GIT_ALTERNATE_OBJECT_DIRECTORIES=$project/.git/objects
  ```

Read in the sources: the harness of [SWE-bench](https://github.com/SWE-bench/SWE-bench/blob/main/swebench/harness/run_evaluation.py)
keeps the repository with its `.git` in the image and applies the patch inside the container with
`git apply`, falling back to `patch`. A comment in that file says that its evaluation script
removes the test files and applies them again; the script itself was not read.

From memory, not checked: that `--attr-source` appeared in git 2.40. Reasoning, without a test:
that one port serves better than two (history apart from trees); that a project whose version
comes only from `setuptools-scm` fails to build without `.git` (cachetools declares it but takes
its version from the source, checked); that a file kept in Git LFS is extracted as its pointer.

## Alternatives considered

- **The runtime builds a commit**, as the module map says. The parent side and the base plus patch
  are not commits.
- **Apply the patch and the tests inside the container**, as SWE-bench does. It needs git in the
  image and a writable tree, and the digest of what ran would be computed inside the zone that
  runs code of others.
- **Extract with `git archive`.** The attributes of the project change what is extracted, so the
  directory is not the tree its digest names.
- **Compose in the `.git` of the project.** Simpler, and it writes objects in the repository of the
  person.
- **Two ports**, one for the history and one for the trees. Both talk to the same repository with
  the same tool; the split can be made later if a second adapter needs it.

## Consequences

- What was built and what the evidence names are the same tree, whatever the attributes of the
  project or the configuration of the person.
- The adapter needs a git with `--attr-source`; an older git is refused.
- A project that needs `.git` to build or to run its tests cannot be verified as it is; its pack
  has to supply what is missing, for example a version for `setuptools-scm`.
- The objects directory of each run is the harness's to clean.
- `platform` gains one more adapter, and the port of the verification runtime changes its contract.
