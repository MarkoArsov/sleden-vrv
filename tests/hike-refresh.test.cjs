const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// Execute the real load method without needing the page's JSX renderer.
const page = fs.readFileSync('index.html', 'utf8');
const loadSource = page.slice(page.indexOf('  load(background) {'), page.indexOf('\n  club(key) {'));
function harness() {
  const requests = [];
  const Component = vm.runInNewContext(`(class { ${loadSource} })`, {
    fetch: () => new Promise((resolve, reject) => requests.push({ resolve, reject })),
    console: { info() {} }, Date,
  });
  const app = new Component();
  app.props = {};
  app.state = { status: 'loading', data: null };
  app.setState = update => Object.assign(app.state, update);
  app.resetDetailMedia = () => ({});
  app.normalizePayload = data => data;
  app.defaultShowPast = () => false;
  return { app, requests };
}
const settle = () => new Promise(resolve => setImmediate(resolve));
const response = label => ({ ok: true, json: async () => ({ generatedAt: label, hikes: [] }) });

test('an older response cannot replace a newer completed refresh', async () => {
  const { app, requests } = harness();
  app.load();
  app.load(true);
  requests[1].resolve(response('new'));
  await settle();
  requests[0].resolve(response('old'));
  await settle();
  assert.equal(app.state.data.generatedAt, 'new');
});

test('a failed foreground refresh preserves visible data', async () => {
  const { app, requests } = harness();
  app.state = { status: 'ok', data: { generatedAt: 'saved', hikes: [] } };
  app.load(true);
  requests[0].reject(new Error('offline'));
  await settle();
  assert.equal(app.state.status, 'ok');
  assert.equal(app.state.data.generatedAt, 'saved');
});

test('overlapping initial and background failures cannot leave loading stuck', async () => {
  const { app, requests } = harness();
  app.load();
  app.load(true);
  requests[0].reject(new Error('offline'));
  requests[1].reject(new Error('offline'));
  await settle();
  assert.equal(app.state.status, 'error');
});
