# inspireauth10: notes for coding agents

The instructions for any AI assistant working in this repository are in [`CLAUDE.md`](CLAUDE.md): read it
first. The step-by-step guides it names are plain Markdown in `.claude/skills/<name>/SKILL.md` (start with
`fork-setup` in a new clone or fork); follow them whether or not your tool loads skills.

The rules, in short:

- No large files in git: `data/` and `out/` come from Google Drive with `python reproduce/get_data.py`.
- No GitHub release, and no new or re-enabled workflow, unless the owner of the repository asks.
- Ask the user before pushing to `gh-pages`, uploading to Drive or merging a pull request.
- Read the tables line by line; work with the shared topic clustering unless asked to recluster.
