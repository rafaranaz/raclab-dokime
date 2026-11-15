# Requirements of the `corpus` scope

The packs of the three repositories of the corpus and the tests that self-check each project at
its commit ([ADR-0052](../adr/0052-the-corpus-runs-in-ci-in-a-job-of-its-own-with-the-network.md)).
A pack is ours; the code of a project is not copied, it is named by its repository and its commit.
The self-checks need the network, so they run only when asked for, in the job `corpus` of CI. Each
requirement follows an EARS template and has at least one test that declares it in its `SDD-EARS:`
marker.

## The files of a project

- **CORPUS-001** The directory of each project of the corpus shall hold only its `pack.yaml`, its `Dockerfile` and its `source.toml`.
- **CORPUS-002** The `source.toml` of each project shall give the address of its repository and the full name of its commit.
- **CORPUS-003** The pack of each project shall pass the check of packs.
- **CORPUS-004** The Dockerfile of each project shall name its base image by its digest.
- **CORPUS-005** The Dockerfile of each project shall install every package with an exact version and without resolving dependencies of its own.

## The self-check of a project

- **CORPUS-010** When the self-checks of the corpus are asked for, the test of each project shall clone its repository with its whole history and run `dokime env check` at its commit with its pack.
- **CORPUS-011** When the self-check of a project ends, the test shall demand the verdict `PASS`.
- **CORPUS-012** When the self-check of a project ends, the test shall demand that no container and no temporary directory of the run is left.
- **CORPUS-013** If cloning the repository of a project fails, then the test shall fail with a message that starts with `network:` and names the address.
- **CORPUS-014** If the self-checks of the corpus are not asked for, then the test of each project shall skip.
