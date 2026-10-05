# Troubleshooting

[README](../README.md) · [Setup](LOCAL_SETUP.md) · [Tiếng Việt](HUONG_DAN_CAI_DAT.md)

Start with the failing component and the log named by the launcher. Commands below assume PowerShell at the repository root.

## The launcher stops during prerequisites

Open Docker Desktop and wait for its engine. Check tool availability:

~~~powershell
docker version
docker compose version
java -version
node --version
py -3.12 --version
~~~

Use JDK 21, Python 3.12, and Node 22.13+ compatible with the lockfile. Install dependencies with the commands in [local setup](LOCAL_SETUP.md#2-clone-and-install). Open a new terminal after changing PATH.

## Port conflict

The launcher refuses to stop a process it cannot identify as belonging to this project. Inspect the reported port and process first:

~~~powershell
$taskPort = 8000
Get-NetTCPConnection -State Listen -LocalPort $taskPort |
    Select-Object LocalAddress, LocalPort, OwningProcess
Get-CimInstance Win32_Process -Filter "ProcessId = REPLACE_WITH_REPORTED_PID" |
    Select-Object ProcessId, Name, CommandLine
~~~

Replace the PID placeholder before running the second command. Stop the conflicting service using its own terminal or owner command. Do not kill every Python, Java, or Node process.

A common cause is starting the complete Compose stack and the host launcher together. The launcher only needs the Compose infrastructure services; its AI runtime runs on the host. If you started a containerized AI runtime separately, stop that known container before relaunching.

## Phone cannot open the app

1. Connect phone and computer to the same Wi-Fi; check that the network does not isolate devices.
2. Keep the launcher and student terminal open. Scan the current QR, not an older screenshot.
3. On the phone, open `http://COMPUTER_LAN_IP:8081/status` in a browser. `packager-status:running` proves the student server is reachable.
4. If it is unreachable, review the computer's private-network firewall permission for the student server. Do not disable the firewall globally.
5. Use an Expo Go client compatible with SDK 57. A client mismatch is separate from a network problem.

To restart the owned student server workflow, use:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-student-metro.ps1
~~~

The student launcher can reuse a healthy owned server. If it reports a conflicting process, resolve that conflict before retrying.

## The app opens but cannot log in

Check business API health:

~~~powershell
Invoke-RestMethod http://localhost:8080/actuator/health
~~~

On a phone, use the computer's LAN address for API connectivity. The app normally resolves the development host automatically. If an override is necessary, set `EXPO_PUBLIC_API_OVERRIDE=http://COMPUTER_LAN_IP:8080/api/v1` in `apps/student-mobile/.env.local` and restart the student server. Keep the API prefix; `EXPO_PUBLIC_API_BASE_URL` is a lower-priority fallback.

Use an account with the student role. [Development accounts](LOCAL_SETUP.md#development-only-accounts) are seeded only in the dev profile; an existing database may have different credentials. A 401 response is an authentication problem, not proof of OCR failure.

## The page is read but no guided lesson starts

Check the entire question: missing givens, multiple problems, or an incorrect OCR number can prevent a valid plan. Use **Chỉnh đề bài** to correct the text.

Some patterns have validated built-in plans; other requests depend on cloud generation. If the runtime returns unavailable, check server-side provider configuration, model access, network, and quota. A selected practice activity does not guarantee that every wording currently has a supported plan.

The demonstration's digit-append problem in [DEMO_GUIDE.md](DEMO_GUIDE.md#guided-lesson-demo) has a built-in plan. Use it to distinguish working lesson infrastructure from an unavailable cloud-dependent request.

## OCR is missing, empty, or inaccurate

Verify which path you are testing:

| Symptom | Check |
| :--- | :--- |
| Main guide cannot read a photographed question | Configured Groq/Gemini access; this path uses cloud vision |
| Handwriting line OCR cannot load its model | CRNN checkpoint path and hash in the [setup guide](LOCAL_SETUP.md#enable-real-recognition-and-guidance) |
| Lines are merged, missing, or overlap a diagram | Crop one problem, straighten the page, improve lighting, review detector configuration |
| Only fixture results appear in async grading | `RUNTIME_MODE=FIXTURE` is synthetic; enable model mode with the correct artifact |

Do not switch to fixture mode and describe the resulting output as recognition of the uploaded handwriting. Preserve the failing sample privately and report the expected lines.

## AI settings changed but behavior did not

Restart services after editing `ai/runtime/.env.local`. Process environment values take precedence over dotenv files. Confirm enabled providers have real keys; placeholder strings are not credentials.

Do not paste keys, authorization headers, student photos, or complete private logs into a public issue. Share sanitized error messages and a non-private reproduction.

## Find logs and check health

~~~powershell
.\scripts\health-check.bat
Get-ChildItem .\infra\local-runtime\logs -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 10 Name, LastWriteTime
~~~

The readiness endpoint checks selected runtime dependencies. A green result does not prove OCR weights, cloud quota, or content correctness.

## Stop or recover

~~~powershell
.\scripts\stop-all.bat
.\RUN_MATHVISION.bat
~~~

Normal stop keeps stored data. Data-reset scripts delete local database/storage data and are not a routine fix for a UI, camera, or provider error.

For a bug report, include the exact action, relevant service, sanitized error, expected result, and a small reproducible sample. See [CONTRIBUTING.md](../CONTRIBUTING.md).
