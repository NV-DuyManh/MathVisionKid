# Demo walkthrough and app gallery

[README](../README.md) · [User guide](USER_GUIDE.md) · [Local setup](LOCAL_SETUP.md)

Use this walkthrough to present the current student experience. Screens below show actual app UI, not generated interface mockups.

## A five-minute tour

| Moment | Show | Explain |
| :--- | :--- | :--- |
| Welcome | Student home | The camera is the primary action; saved work, practice, and progress are easy to reach |
| Practice | Lesson library, grades 1–5 | Choose a grade and a question; the labels describe selected practice topics |
| Read a photo | One clear problem | Crop, privacy review, editable transcription, then a guided lesson |
| Think | A supported guided example | The learner chooses a method and calculates each result |
| Reflect | Completed steps | The solution is built from the learner's attempts |
| Continue | Saved work and progress | Current learning history is stored on the device |

For a reliable presentation, verify services and required capabilities beforehand. An unavailable provider should be described honestly; do not replace its output with unlabeled fixtures.

## Guided lesson demo

The digit-append example has a validated built-in plan. It exercises lesson infrastructure without requiring a generated cloud plan. It still needs a running business API, AI runtime, and authenticated student session.

1. Open **Bài học**, select a practice card's **Cùng em tìm cách giải**.
2. Choose **Chỉnh đề bài** and replace the text with the example below.
3. Choose **Dùng nội dung này**, then **Bắt đầu từng bước**.
4. Answer the steps and compare the completed solution.

> Tìm một số biết rằng nếu viết thêm chữ số 6 vào bên phải số đó ta được số mới lớn hơn số phải tìm 537 đơn vị.

Presenter reference:

| Step | Reasoning | Input |
| :--- | :--- | :--- |
| Understand the new number | Appending a digit multiplies the original number by ten, then adds the digit | Gấp lên rồi cộng chữ số mới |
| Count the additional parts | Ten equal parts minus the original part | 9 |
| Remove the appended digit | 537 − 6 | 531 |
| Find the original number | 531 ÷ 9 | 59 |
| Verify | 59 × 10 + 6 − 59 | 537 |

This is a lesson demonstration with typed input. It is **not** a benchmark of photo transcription or line detection.

## Photo demo

On a phone, choose **Chụp bài toán** and use a non-private handwritten sample. Take one problem per photo, straighten and crop it, cover private information, and compare every recognized number and symbol against the image.

If only a worked solution is photographed, add the original problem. If the app reports multiple problems or unclear content, recrop rather than treating incomplete text as a complete question.

Main-guide photo transcription requires configured cloud vision. To demonstrate the separate CRNN line OCR path, install its checkpoint and use the handwriting workflow/endpoints appropriate to that feature. See [recognition boundaries](ARCHITECTURE_LOCAL_RUNTIME.md#three-different-recognition-tasks).

## App gallery

<table>
  <tr>
    <td align="center"><a href="media/screenshots/home-web.jpg"><img src="media/screenshots/home-web.jpg" width="260" alt="Student home" /></a><br /><strong>Home</strong></td>
    <td align="center"><a href="media/screenshots/lessons-web.jpg"><img src="media/screenshots/lessons-web.jpg" width="260" alt="Grade five lesson library" /></a><br /><strong>Practice library</strong></td>
    <td align="center"><a href="media/screenshots/guided-step-web.jpg"><img src="media/screenshots/guided-step-web.jpg" width="260" alt="A guided reasoning question" /></a><br /><strong>Guided reasoning</strong></td>
  </tr>
  <tr>
    <td align="center"><a href="media/screenshots/problem-android.png"><img src="media/screenshots/problem-android.png" width="260" alt="Android photo transcription supplied by the owner" /></a><br /><strong>Photographed question</strong></td>
    <td align="center"><a href="media/screenshots/completed-lesson-web.jpg"><img src="media/screenshots/completed-lesson-web.jpg" width="260" alt="Completed steps in a guided lesson" /></a><br /><strong>Completed lesson</strong></td>
    <td align="center"><a href="media/screenshots/progress-web.jpg"><img src="media/screenshots/progress-web.jpg" width="260" alt="Learning progress in its initial state" /></a><br /><strong>Progress</strong></td>
  </tr>
</table>

Click an image to view its original capture. Long screens show the visible portion of scrollable content.

## Screenshot provenance

| Asset | Source | Context |
| :--- | :--- | :--- |
| `home-web.jpg` | Local student web preview, 5 Oct 2026 | 390 × 844 viewport; actual initial home |
| `lessons-web.jpg` | Same preview session | Grade five selected; no invented activity |
| `guided-step-web.jpg` | Same preview session | First step of the typed digit-append example |
| `completed-lesson-web.jpg` | Same preview session | Real completion after answering all five steps |
| `progress-web.jpg` | Same preview session | Empty saved-history state; metrics were not fabricated |
| `problem-android.png` | Owner-supplied Android attachment | Existing capture showing photo + transcription; not a new physical-device test |
| `readme-hero.jpg` | [HTML presentation source](media/showcase.html) | Brand composition using actual web captures and existing mascot assets |

The screenshots do not establish that every device or every question works. This documentation task captured the web experience and reused one supplied Android capture. It did not repeat a physical-device camera test.

## Recreate the cover

Serve the repository locally, open `docs/media/showcase.html`, and capture its 1600 × 860 artwork at 100% scale after fonts and images load. The cover uses the app's existing Nunito font, purple/navy palette, star mascot, and screenshots. No generated app UI is used.

Keep source screenshots and provenance together when refreshing the cover. Replace screenshots after significant UI changes and recheck both the README and gallery.
