// Give one request to swarm-verify, pinned by package-lock.json, and write its result (R2).
//
//   node run_arm.mjs < REQUEST.json
//
// The request gives `repository`, `base`, `candidate` (a commit), `image`, `out` (the directory of
// the evidence), `checks` (the supplied checks) and `sealed`: null, or the `files` to seal, each a
// `path` and its `content` as text, with the `checks` that run them. The sealed files come only
// through the input, and are sealed with sealFiles from memory into the SWARM_HOME of the process.
import { requestVersion, sealFiles, verifierVersion, verify } from "swarm-verify";

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const given = JSON.parse(Buffer.concat(chunks).toString("utf8"));

if (given.sealed) {
  await sealFiles({
    workspace: given.repository,
    files: given.sealed.files.map((file) => ({
      path: file.path,
      content: Buffer.from(file.content, "utf8"),
    })),
    checks: given.sealed.checks,
    authority: "user-acceptance",
  });
}

const result = await verify(
  {
    version: requestVersion,
    repository: given.repository,
    base: { commit: given.base },
    candidate: { kind: "commit", commit: given.candidate },
    requirements: [],
    checks: given.checks,
    policy: { execution: { mode: "isolated", dependencies: "prepare", image: given.image } },
    artifacts: { directory: given.out },
  },
  { verifierVersion },
);
process.stdout.write(JSON.stringify(result));
