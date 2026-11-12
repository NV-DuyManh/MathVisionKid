import assert from 'node:assert/strict';
import { createServer } from 'node:http';

assert.equal(process.env.MATHVISION_LIVE_DISPOSABLE, 'true', 'Explicit disposable environment required');
const jobsPath = '/internal/v1/jobs';
const fault = process.env.MATHVISION_LIVE_AI_FAULT ?? 'dispatch';
assert(['dispatch', 'retake'].includes(fault), 'Choose dispatch or retake fault');
let firstDispatch = true;

createServer(async (request, response) => {
  if (request.method !== 'POST' || request.url !== jobsPath) {
    response.writeHead(404).end();
    return;
  }
  try {
    const chunks = [];
    for await (const chunk of request) chunks.push(chunk);
    if (fault === 'dispatch' && firstDispatch) {
      firstDispatch = false;
      console.log('Injected one HTTP 503 before forwarding the job');
      response.writeHead(503).end();
      return;
    }
    let body = Buffer.concat(chunks);
    if (fault === 'retake') {
      const job = JSON.parse(body);
      if (typeof job.imageReference === 'string' && job.imageReference.includes('quality-fail-worksheet')) {
        job.imageReference = 'fixture://empty-image';
        body = JSON.stringify(job);
      }
    }
    const forwarded = await fetch('http://127.0.0.1:18001' + jobsPath, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
      signal: AbortSignal.timeout(10000),
    });
    response.writeHead(forwarded.status, { 'Content-Type': 'application/json' }).end(await forwarded.text());
  } catch {
    response.writeHead(502).end();
  }
}).listen(18002, '127.0.0.1', () => console.log(fault + ' fault fixture ready on loopback'));
