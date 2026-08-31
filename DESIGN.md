# Weather Forecast

## Project structure

```text
data/               Raw data downloads and processed image outputs
salesforce/         Salesforce metadata for deployment
src/
  weather_forecast/
    cli.py          entry point, registered as the `weather-forecast` command
                      via [project.scripts] in pyproject.toml
                      banner, command table, slot reading, dispatch
    args.py         parser, exit codes, USAGE, and the version lookup
    cli_run.py      the run command: its docs, env check, and pipeline call
    chart/          PDF download, PNG conversion, image resizing
    forecast/       vision model inference (WeatherVision)
    orchestration/  pipeline coordinator (WeatherPipeline)
    salesforce/     Salesforce JWT auth and Weather_Report__c upsert
tests/              Test suite for the weather forecast application
```

## Command line

The grammar is `weather-forecast COMMAND [--flags]`.

```text
weather-forecast run [--force | --dryrun]
weather-forecast version
weather-forecast --version
```

`--force` and `--dryrun` belong to `run` and are mutually exclusive.

Execution takes a command word, never a flag. A flag the tool refuses to work
without is a command word wearing the wrong clothes, and it sits in the wrong
slot besides.

Nothing runs by accident. Bare `weather-forecast` prints the banner and
touches nothing, so reaching the pipeline takes a word typed on purpose.

### A lone command word acts here

House style answers a lone command word with that command's documentation,
exit 0. The rule catches an incomplete line, a command typed without the
argument it operates on. Neither command here takes an argument. `run` alone
and `version` alone are complete lines, so both act.

That is the only divergence, and it costs nothing. What a per-command
docstring would have carried is the flag list, which the banner already
prints.

### `version` and `--version`

Both spellings print the program name and the installed version on one line,
then exit 0. It is documentation, so it shares its exit code with the banner.

One helper builds that line and both spellings call it. Two independent prints
of the same fact drift apart, and this is a fact where drift stays invisible
until someone reports the wrong number.

The number is read from the installed distribution metadata, which keeps
`pyproject.toml` the only copy. A tree that has never been built has no
metadata to read, so the lookup is guarded and answers
`unknown (not installed)` instead of raising. The guard matters because the
parser is built on every invocation past a bare word, so an unguarded lookup
would take down `run` as well.

`--version` is defined on the top-level parser only. Asking `run` for the
version is an unknown flag, exit 2.

Neither spelling is advertised. The banner carries the work the tool does, and
a version number is not that. Anyone who wants one goes looking, and this is
where the looking ends.

### Positions are decided, not inferred

Neither command takes a positional, so any bare word after the command is a
stray. `main` reads the slot off the front of the command line with the house
helper instead of trusting what argparse resolved from elsewhere. The helper
keeps its house name, `leading_paths`, so it stays recognizable across the
toolchain, even though nothing it finds here is a path. A stray gets
weather-forecast's own error with the usage line under it, exit 1.

### Layout

`args.py` sits beside `cli.py` and holds the parser, the exit codes, the
version lookup, and the one `USAGE` line. The whole grammar fits on that
line, so both commands share it instead of carrying one each.

`cli_run.py` holds the run command's own documentation, the environment check,
and the call into the pipeline. Logging is configured there rather than in
`main`, which is what lets `version` answer with one line and no log preamble
above it.

`version` gets no module. It is one print, and it stays in `cli.py` beside the
command table.

`cli.py` keeps the banner, the command table, the slot reading, the usage
error, and `main`.

The accepted grammar is pinned in a test file of its own. A command line that
drifts from the documented shape still parses, it just means something else,
so nothing fails on its own when the surface moves.

### Exit codes

0 covers success, a run skipped because the PDF is unchanged, and
documentation, which is the banner and both version spellings. 1 is
weather-forecast's own error: a stray token, a missing environment variable,
or a pipeline failure. 2 is argparse's own: an unknown command, an unknown
flag, or a bad value. Only 0 and 1 return through `main`.

## Vision model

`HuggingFaceTB/SmolVLM2-500M-Video-Instruct` replaces
`llava-hf/llava-interleave-qwen-0.5b-hf`.

State the bar first, because it decides everything below it. The prompt asks
"What is this?". The run is a success if the answer describes a weather chart.
Nothing in this project forecasts anything, despite the name. The chart is a
JMA surface analysis, and the model is reading it, not interpreting it.

Memory picks the model. The machine is an M1 MacBook Air with 8 GB. Weights on
disk, measured rather than guessed from the parameter count:

| model | bytes | stored as |
| --- | --- | --- |
| llava-interleave-qwen-0.5b-hf | 1.73 GB | fp16 |
| SmolVLM2-500M-Video-Instruct | 2.03 GB | fp32 |
| SmolVLM2-2.2B-Instruct | 8.99 GB | fp32 |

The 2.2B is the interesting one and it stays on the shelf. It does not fit at
full width, and every route to a quantized copy leaves torch behind: the MLX
build needs `mlx-vlm`, the GGUF build needs llama.cpp, and bitsandbytes has no
working MPS backend. That is a runtime decision, not a model decision, and it
deserves its own round.

The odd name is upstream. SmolVLM2 ships its small sizes only as
`-Video-Instruct`. Still images are fine.

The licence improves on the way through. SmolVLM2 is Apache 2.0. The outgoing
model carried the Tongyi Qianwen Research License, which is non-commercial, so
the restriction leaves with it.

### Why the prompt stays short

"What is this?" is the whole prompt, and asking for more makes the answer
worse. Prompts that requested analysis produced a temperature of 20°C, a
pressure of 1000 mb, and a storm near Guam. None of that is on a surface
analysis in any form this model could read. Two prompts run against the same
image then disagreed on whether the weather was clear or overcast, which is
what settles it. The figures come from the question, not from the page.

So the prompt asks the one thing the model can answer from pixels, and the
answer names the JMA. The longer prompts were also three to five times slower,
and they tended to hit the token cap partway through repeating themselves.

### The full render, never the thumbnail

The processor splits the image into sub-crops and emits a fixed token budget
either way, so a smaller source image buys nothing and costs signal. Fed the
300px thumbnail, the model called a JMA surface analysis a map of the United
States. Fed the full render, it named the JMA. Splitting stays on for the same
reason: turned off, the whole chart collapses to 79 tokens and the answer
wanders off to the Pacific Ocean and repeats itself until the token cap.

The pipeline already passed the full render. That is now a requirement rather
than a coincidence, and it is written on `_generate_forecast`.

### `num2words` is a real dependency

SmolVLM2's processor imports it and raises on `from_pretrained` without it.
Nothing in the project imports it by name, so it is pinned in `pyproject.toml`
alongside `docopt`, which it pulls in turn. Both are as load-bearing as
`cryptography`, and as easy to prune by mistake.

### The prompt is built by the processor now

LLaVA's processor takes raw text, counts the literal `<image>` placeholders in
it, and expands each one. SmolVLM2 works the other way. It splits the image
into sub-crops first, then `apply_chat_template` emits however many image
tokens that produced. A hand-written `<image>` cannot know the count, so the
placeholder goes and the template builds the prompt.

Decoding follows from the same change. A chat template puts the user turn
inside the output sequence, so decoding the whole thing hands back the prompt
along with the answer. Only the generated tail is decoded.

### `WF_VISION_MODEL` is removed

The variable read as "point this at any vision model". What it actually
selected was any model whose processor accepts raw text containing `<image>`,
which is the LLaVA family and little else. Pointing it at SmolVLM2 produces a
token count mismatch, not a forecast. An override that fails on the next model
anyone would reach for is worse than no override, because it invites the
attempt.

The model id returns to a single constant in `generator.py`.

### The title split goes

The old prompt asked for "Title and description" and the pipeline split the
answer on its first newline into `title` and `content`. Only `content` was ever
published. `_publish_salesforce` passes `forecast["content"]` and nothing else,
and the record `Name` is a fixed string set inside `upsert_report`. The split
has been discarding the model's first line the whole time.

So the split goes and the whole answer becomes the content. Nothing builds a
title, because nothing ever consumed one, and the record name stays the fixed
string it already was.

## Dependencies

Dependencies are declared once, in `pyproject.toml`. The three requirements
files are removed. `requirements.txt` listed the seven runtime roots unpinned,
`requirements-dev.txt` listed the test tooling unpinned, and
`requirements-pinned.txt` held a freeze. All three restated what
`[project.dependencies]` already carried, and the freeze had already drifted a
day out of step with it.

`[project.dependencies]` keeps the full pinned set, transitive entries
included. That is a lockfile living in the dependency table, and it is
deliberate: a proof of concept pinned to one tested combination is worth more
than one that resolves freshly and stops working.

`[dependency-groups]` holds a `dev` group, in the shape every project in the
toolchain uses: `black` and `ruff` pinned, `pytest`, `pytest-cov`, and
`pytest-mock` left to float. The split is on purpose. A formatter that moves
underneath you reformats the tree on its own, so it is pinned. A test runner
does not, so it is not.

The group is not a second freeze. `iniconfig`, `pluggy`, and `Pygments` reach
an install only through pytest. They leave `[project.dependencies]` and do not
reappear in the group, because pip resolves them. What moving the test tooling
out buys is a `pipx` install of the command that no longer carries a test
runner.

Installing:

```bash
pip install -e .                # runtime only
pip install -e . --group dev    # runtime plus the tests
```

`--group` arrived in pip 25.1, so an older pip cannot read the group.

`cryptography` looks unused and is not. It reaches the project through
PyJWT's `crypto` extra, which RS256 signing needs, and the JWT handshake signs
with RS256. Nothing imports it by name, so it survives only if whoever prunes
this table knows why it is there.

## Use of AI

Both the use of AI and its disclosure are deliberate. Code and
documentation in this project are written in collaboration with
Artificial Intelligence (AI). The division of labour: the AI explores,
challenges assumptions and edge cases, and drafts; the human
initiates, drafts the designs, explores alongside the AI, reviews
every change, and decides what gets committed.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
