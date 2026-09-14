# weather-forecast design

## Project structure

```text
data/               raw data downloads and processed image outputs
salesforce/         Salesforce metadata for deployment
scripts/            scheduled-run template and org storage cleanup
src/
  weather_forecast/
    args.py         parser, exit codes, USAGE, and the version lookup
    cli.py          entry point, the `weather-forecast` command via
                      [project.scripts]: banner, command table, slot
                      reading, dispatch
    cli_run.py      the run command: its docs, env check, and pipeline call
    chart/          PDF download, PNG conversion, image resizing
    forecast/       vision model inference (WeatherVision)
    orchestration/  pipeline coordinator (WeatherPipeline)
    salesforce/     Salesforce JWT auth and Weather_Report__c upsert
tests/              test suite for the weather forecast application
```

### Why the CLI is three files

`args.py` holds the parser, the exit codes, the version lookup, and the one
`USAGE` line. The whole grammar fits on that line, so both commands share it
instead of carrying one each.

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

JMA updates it three times a day. A run scheduled more often than that mostly
finds the chart it already has, and that costs a download and nothing else.

The PDF is a single A3 landscape page, about 550 KB, holding nothing but the
chart. Page one rendered to PNG is the whole document, and the model reads the
PNG, never the PDF. `pdf2image` does the rendering through poppler, at its
default 200 dpi. That gives 3309 × 2339 pixels and a PNG of about 1.7 MB.

Where the files land depends on how the command was installed. A pipx install
writes to `~/.cache/weather-forecast/data/`, since a pipx user has no checkout
to write into. Every other install writes to `./data` under the working
directory.

Two PDFs are kept, `current.pdf` and `last.pdf`. Comparing their hashes is the
only thing that decides whether a run has new work to do. `current.pdf` rotates
to `last.pdf` before every download. A download that hashes the same as
`last.pdf` is deleted again, and `last.pdf` answers in its place.

The hash is SHA-256 over the file's bytes. The same 64-character hex string is
the record's key in Salesforce. One number decides both whether to run and
which record to write.

## Vision model

The model is `HuggingFaceTB/SmolVLM2-500M-Video-Instruct`.

The bar comes first, because it decides everything below it. The prompt asks
"What is this?". The run is a success if the answer describes a weather chart.
Nothing in this project forecasts anything, despite the name. The chart is a
JMA surface analysis, and the model is reading it, not interpreting it.

Memory picks the model. The machine is an M1 MacBook Air with 8 GB. Weights on
disk, measured rather than guessed from the parameter count:

| model | bytes | stored as |
| --- | --- | --- |
| SmolVLM2-500M-Video-Instruct | 2.03 GB | fp32 |
| SmolVLM2-2.2B-Instruct | 8.99 GB | fp32 |

The 2.2B is the interesting one, and it stays on the shelf. It does not fit at
full width, and every route to a quantized copy leaves torch behind: the MLX
build needs `mlx-vlm`, the GGUF build needs llama.cpp, and bitsandbytes has no
working MPS backend. That is a runtime decision, not a model decision.

No `dtype` is passed on load, so the 500M loads as shipped, in fp32. It runs
on MPS, Apple Silicon's GPU backend for torch, and falls back to the CPU where
MPS is missing. The processor and the model load once per run.

The odd name is upstream. SmolVLM2 ships its small sizes only as
`-Video-Instruct`. Still images are fine.

The licence is Apache 2.0.

### Why the prompt stays short

"What is this?" is the whole prompt, and asking for more makes the answer
worse. Prompts that requested analysis produced a temperature of 20°C, a
pressure of 1000 mb, and a storm near Guam. None of that is on a surface
analysis in any form this model could read. Two prompts run against the same
image then disagreed on whether the weather was clear or overcast. That settles
it: the figures come from the question, not from the page.

So the prompt asks the one thing the model can answer from pixels, and the
answer names the JMA. The longer prompts were also three to five times slower,
and they tended to hit the token cap partway through repeating themselves. The
cap is 150 new tokens.

### The full render, never the thumbnail

The processor splits the image into sub-crops and emits a fixed token budget
either way, so a smaller source image buys nothing and costs signal. Fed the
300px thumbnail, the model called a JMA surface analysis a map of the United
States. Fed the full render, it named the JMA. Splitting stays on for the same
reason. Turned off, the whole chart collapses to 79 tokens, and the answer
wanders off to the Pacific Ocean and repeats itself until the token cap.

The full render is a requirement, not a convenience, and the docstring on
`_generate_forecast` says so.

### The prompt is built by the processor

SmolVLM2 splits the image into sub-crops first, and `apply_chat_template` then
emits however many image tokens that produced. A hand-written `<image>`
placeholder cannot know that count, so the template builds the prompt and no
literal placeholder appears in the text.

Decoding follows from the same fact. A chat template puts the user turn inside
the output sequence, so decoding the whole thing hands back the prompt along
with the answer. Only the generated tail is decoded.

### `num2words` and `torchvision` are real dependencies

SmolVLM2's processor imports `num2words` and raises on `from_pretrained`
without it. Nothing in the project imports it by name, so it is pinned in
`pyproject.toml` alongside `docopt`, which it pulls in turn.

`torchvision` is the same trap one level up. `processing_smolvlm.py` imports
the video processor at module scope, and that module imports
`torchvision.transforms.v2`. No video is ever processed here and the import
happens anyway, so a build without `torchvision` cannot construct the
processor at all. What it raises is `ModuleNotFoundError: Could not import
module 'SmolVLMProcessor'`. That names the processor and not the missing
package, so the error sends the reader to the wrong place.

All three are as load-bearing as `cryptography`, covered under Dependencies,
and as easy to prune by mistake.

## Salesforce

The generated text and a preview image land on a `Weather_Report__c` record
through `simple_salesforce`, a thin REST API client. Nothing heavier sits in
the way: no MuleSoft, no data loader, no middleware. One record per chart does
not need a platform behind it.

Salesforce stays passive. The project deploys no Apex, no flows, and no
triggers, only the object and a permission set. Every write comes from the
pipeline.

### The record

`PDF_Hash__c` is a 64-character text field, marked as an external ID and
unique. The upsert keys on it, as one PATCH to a URL that names both the field
and the value:

```text
PATCH /services/data/v59.0/sobjects/Weather_Report__c/PDF_Hash__c/<sha256>
```

The version is `simple_salesforce`'s default, since the client passes none. A
new chart creates a record, and a chart seen before updates the record it
already has. So `--commit --force` on an
unchanged chart rewrites the forecast in place, which is the `created=False`
in a run's log.

`simple_salesforce` answers an upsert with the HTTP status alone, 201 for a
create. The record id is not in the answer, so a SOQL query by hash fetches it
afterwards. That is two round trips, and the second cannot come back ambiguous
because the field is unique.

Every SOQL query is built by string formatting, with no escaping. That holds
because nothing typed by a person reaches one. The values are a hex digest the
pipeline computed and record ids Salesforce itself handed back.

Every record is named `DEV Weather Report`. What tells them apart at a glance
is `PDF_Hash_4_4__c`, a formula field showing the first four and last four
characters of the hash, like `1ffd..33b5`. A full hash is too wide for a list
view, and eight characters are plenty for a few charts a day.

`Forecast__c` is a long text area of 32,768 characters. A 150-token answer
never comes near it.

Two fields carry `DEPRECATED` in their labels, `Chart_Image_Id__c` and
`Import_Timestamp__c`. Nothing writes them.

### The preview image

The image is the 300px-wide thumbnail, resized with Lanczos to 300 × 212 and
about 93 KB. The model and Salesforce get opposite files. The model needs the
full render to read the chart, and Salesforce needs the thumbnail to stay
inside its storage.

It goes up as a `ContentVersion`, base64 in the JSON request body, which puts
about 124 KB on the wire for a 93 KB file. `FirstPublishLocationId` links it to
the record in the same insert, so no separate `ContentDocumentLink` is ever
written.

Before uploading, the client lists the files linked to the record and reads
the newest version's title on each. Salesforce drops the extension, so the
title to look for is `weather_small`. If it is there, nothing uploads. A record
holds one preview however many times its chart is forced through.

The text goes first and the image second, as two separate calls with no
transaction around them. An upload that fails leaves a record with no preview,
and the run exits 1. The next ordinary run finds the chart unchanged and
skips. `--commit --force` repairs it: the upsert rewrites the text, the title
check finds nothing, and the preview goes up.

File storage is what sizes the thumbnail. A Developer Edition org has about
20 MB of it. The full render would fill that in twelve uploads, four days at
three charts a day. The thumbnail lasts a little over 200 uploads, around ten
weeks. That still runs out, so the metadata ships a `Bulk_API_Hard_Delete`
permission set. It lets old uploads be hard-deleted through the Bulk API,
which skips the Recycle Bin.

The permission set grants that one user permission and nothing else, with no
object or field access. It belongs to whoever clears the storage, not to the
run. The run's own access to `Weather_Report__c` comes from elsewhere.

### OAuth connection

Authentication is Salesforce's OAuth 2.0 JWT Bearer flow. No browser, no
redirect, and no interactive step, which is what lets an unattended run work.
The assertion is signed with RS256 and posted to the org's token endpoint, and
the returned session is handed to `simple_salesforce`.

The assertion names the client id as issuer, the username as subject, and the
audience, and it expires after five minutes. Each run signs a fresh one, so no
token is stored between runs.

The audience is a login host, and the org lives somewhere else. The token
response carries an `instance_url` beside the access token, and the session is
opened there. Nothing after the handshake talks to the audience again.

The org side is set up before the first run: a connected app, a certificate,
and the four `SF_*` environment variables carrying the username, client id,
audience, and private key. Those variables are read from the environment and
from nowhere else, so weather-forecast never keeps a credential of its own.

## Dependencies

Dependencies are declared once, in `pyproject.toml`. There are no requirements
files. A requirements file restates what `[project.dependencies]` already
carries, and a freeze kept beside the table drifts out of step with it within
days.

`[project.dependencies]` keeps the full pinned set, indirect entries included.
That is a lockfile living in the dependency table, and it is deliberate. A
proof of concept pinned to one tested combination is worth more than one that
resolves freshly and stops working.

`[dependency-groups]` holds a `dev` group, in the shape every project in the
toolchain uses: `black` and `ruff` pinned, `pytest`, `pytest-cov`, and
`pytest-mock` left to float. A formatter that moves underneath you reformats
the tree on its own, so it is pinned. A test runner does not, so it is not.

The group is not a second freeze. `iniconfig`, `pluggy`, and `Pygments` reach
an install only through pytest, so neither the table nor the group names them,
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

Both the use of AI and its disclosure are deliberate. Code and documentation in
this project are written in collaboration with Artificial Intelligence (AI). The
division of labour: the AI explores, challenges assumptions and edge cases, and
drafts; the human initiates, drafts the designs, explores alongside the AI,
reviews every change, and decides what gets committed.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
