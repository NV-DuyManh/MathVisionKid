# Contributing to MathVision Kids

[README](README.md) · [Local setup](docs/LOCAL_SETUP.md) · [Architecture](docs/ARCHITECTURE_LOCAL_RUNTIME.md)

Small, focused improvements with clear evidence are easier to review. Set up the local ecosystem before testing a change.

## Before changing code

Read [AGENTS.md](AGENTS.md), the relevant workspace README, and current contracts. Preserve backend authority for authentication and roles. Keep changes within the requested app or service.

For mobile work, use the exact [Expo SDK 57 documentation](https://docs.expo.dev/versions/v57.0.0/). Keep lockfiles aligned; do not upgrade packages as an unrelated cleanup.

Create a focused branch, describe the user-facing problem, and show how the behavior changes.

## Useful checks

Run the checks relevant to your change. These commands run from the repository root.

**Mobile tests and types**

~~~powershell
npm test --workspace=student-mobile -- --runInBand
.\node_modules\.bin\tsc.cmd --noEmit -p apps/student-mobile/tsconfig.json
~~~

**Web workspace builds**

~~~powershell
npm run build:web
~~~

**AI tests**

~~~powershell
Push-Location ai\runtime
try {
    .\.venv\Scripts\python.exe -m pytest -q tests/test_math_tutor.py tests/test_notebook_tutor.py tests/test_primary_lessons.py tests/test_guided_lesson.py
} finally {
    Pop-Location
}
~~~

The example selects tutoring regression suites that mock cloud calls. Other suites can require optional dependencies, artifacts, or live services. Running the full collection can invoke configured cloud providers; opt into that deliberately and document cost, quota, and prerequisites.

**Backend tests**

~~~powershell
$previousSpringProfile = $env:SPRING_PROFILES_ACTIVE
Push-Location backend\business-api
try {
    $env:SPRING_PROFILES_ACTIVE = 'test'
    .\gradlew.bat test --no-daemon --console=plain
} finally {
    Pop-Location
    if ($null -eq $previousSpringProfile) {
        Remove-Item Env:SPRING_PROFILES_ACTIVE -ErrorAction SilentlyContinue
    } else {
        $env:SPRING_PROFILES_ACTIVE = $previousSpringProfile
    }
}
~~~

Do not claim all tests passed when only selected suites ran. Mention prerequisites and exclusions in the pull request.

## Recognition examples

Provide a non-private image, the exact expected text, and expected line regions when reporting detection or OCR errors. Label human-reviewed ground truth separately from model output. Include empty pages and difficult layouts when relevant, rather than testing only easy examples.

Report line geometry, text quality, and arithmetic correctness separately. Repeatedly testing the same labeled development images is useful for regression, but is not a new held-out accuracy measurement.

Model training needs owner authorization, a documented dataset split, reproducible configuration, and evaluation. A successful detector script or corrected annotation is not evidence that new model weights were trained.

## What belongs in Git

Source, tests, contracts, reviewed public documentation, and approved demonstration media belong in the repository. Private student images, datasets, checkpoints, credentials, local environment files, and runtime logs do not.

Check the staged diff and file list before committing. Do not add secrets even if a filename is not ignored.

## Pull request checklist

- Describe the concrete problem and resulting behavior.
- Include relevant test results and visual evidence for UI changes.
- Identify remaining limitations.
- Preserve third-party notices and licenses.
- Keep demo fixtures clearly labeled as synthetic.
- Avoid putting architecture, development commands, service URLs, or demo account details into student-facing screens.

For security-sensitive reports, contact the repository owner privately through an available channel. Do not publish credentials or exploitable private details in a public issue.
