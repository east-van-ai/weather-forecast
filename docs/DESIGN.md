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

### Why the CLI is three files

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

## The chart

One URL, the JMA quick-look surface analysis:

<https://www.data.jma.go.jp/yoho/data/wxchart/quick/ASAS_COLOR.pdf>

The PDF holds nothing but the chart image, so page one rendered to PNG is the
whole document. The model reads the PNG, never the PDF.

Where the files land depends on how the command was installed. A pipx install
writes to `~/.cache/weather-forecast/data/`, since a pipx user has no checkout
to write into. Every other install writes to `./data` beside the working
directory.

Two PDFs are kept, `current.pdf` and `last.pdf`. Comparing their hashes is the
only thing that decides whether a run has new work to do.

## Vision model

The model is `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`.

State the bar first, because it decides everything below it. The prompt asks
"What is this?". The run is a success if the answer describes a weather chart.
Nothing in this project forecasts anything, despite the name. The chart is a
JMA surface analysis, and the model is reading it, not interpreting it.

Memory picks the model. The machine is an M1 MacBook Air with 8 GB. Weights on
disk, measured rather than guessed from the parameter count:

| model | bytes | stored as |
| --- | --- | --- |
| SmolVLM2-500M-Video-Instruct | 2.03 GB | fp32 |
| SmolVLM2-2.2B-Instruct | 8.99 GB | fp32 |

The 2.2B is the interesting one and it stays on the shelf. It does not fit at
full width, and every route to a quantized copy leaves torch behind: the MLX
build needs `mlx-vlm`, the GGUF build needs llama.cpp, and bitsandbytes has no
working MPS backend. That is a runtime decision, not a model decision, and it
deserves its own round.

The odd name is upstream. SmolVLM2 ships its small sizes only as
`-Video-Instruct`. Still images are fine.

The licence is Apache 2.0.

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

The full render is a requirement, not a convenience, and it is written on
`_generate_forecast`.

### `num2words` and `torchvision` are real dependencies

SmolVLM2's processor imports `num2words` and raises on `from_pretrained`
without it. Nothing in the project imports it by name, so it is pinned in
`pyproject.toml` alongside `docopt`, which it pulls in turn.

`torchvision` is the same trap one level up. `processing_smolvlm.py` imports
the video processor at module scope, and that module imports
`torchvision.transforms.v2`. No video is ever processed here and the import
happens anyway, so a build without `torchvision` cannot construct the
processor at all. What it raises is `ModuleNotFoundError: Could not import
module 'SmolVLMProcessor'`, which names the processor and not the missing
package, so the error sends the reader to the wrong place.

All three are as load-bearing as `cryptography`, and as easy to prune by
mistake.

### The prompt is built by the processor

SmolVLM2 splits the image into sub-crops first, and `apply_chat_template` then
emits however many image tokens that produced. A hand-written `<image>`
placeholder cannot know that count, so the template builds the prompt and no
literal placeholder appears in the text.

Decoding follows from the same fact. A chat template puts the user turn
inside the output sequence, so decoding the whole thing hands back the prompt
along with the answer. Only the generated tail is decoded.

## Salesforce

The generated text is uploaded with `simple_salesforce`, a thin REST API
client, and lands on a `Weather_Report__c` record. Nothing heavier sits in the
way: no MuleSoft, no data loader, no middleware. One record per run does not
need a platform behind it.

### OAuth connection

Authentication is Salesforce's OAuth 2.0 JWT Bearer flow. No browser, no
redirect, and no interactive step, which is what lets an unattended run work.
The assertion is signed with RS256, posted to the org's token endpoint, and
the returned session is handed to `simple_salesforce`.

The org side is set up before the first run: a connected app, a certificate,
and the four `SF_*` environment variables carrying the username, client id,
audience, and private key. Those variables are read from the environment and
from nowhere else, so weather-forecast never keeps a credential of its own.

## Dependencies

Dependencies are declared once, in `pyproject.toml`. There are no
requirements files. A requirements file restates what `[project.dependencies]`
already carries, and a freeze kept beside the table drifts out of step with it
within days.

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
an install only through pytest, so neither the table nor the group names them
and pip resolves them. Keeping the test tooling out of the runtime table is
what lets a `pipx` install of the command carry no test runner.

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
