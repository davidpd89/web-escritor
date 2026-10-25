import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
JS = r'''
const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const handlers = {};
const ctx = {
  URL, Request, Response, Set, console,
  caches: {open: async () => ({match: async () => undefined, put: async () => {}})},
  fetch: async () => new Response('ok'),
  self: {location: {origin: 'https://example.test'}, addEventListener: (n, fn) => handlers[n] = fn}
};
vm.runInNewContext(fs.readFileSync('service-worker.js', 'utf8'), ctx);
function intercepted(path, headers, destination) {
  const request = new Request('https://example.test' + path, {headers});
  if (destination) Object.defineProperty(request, 'destination', {value: destination});
  let called = false;
  handlers.fetch({request, respondWith: () => {called = true}});
  return called;
}
assert.strictEqual(intercepted('/assets/video.mp4', {'Range': 'bytes=0-99'}), false);
assert.strictEqual(intercepted('/assets/sound.mp3', {}, 'audio'), false);
assert.strictEqual(intercepted('/assets/movie.mp4', {}, 'video'), false);
assert.strictEqual(intercepted('/assets/app.css', {}), true);
assert.strictEqual(intercepted('/assets/app.js', {}), true);
console.log('PASS media and range bypass');
'''

class TestMediaBypass(unittest.TestCase):
    def test_bypass(self):
        p = subprocess.run(['node', '-e', JS], cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)

if __name__ == '__main__':
    unittest.main()
