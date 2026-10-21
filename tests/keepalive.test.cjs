const {test} = require('node:test');
const assert = require('node:assert/strict');
const run = require('../scripts/keepalive.cjs');
const now = new Date('2026-10-21T00:00:00Z');
function fixture(state = 'active', date = '2026-09-01T00:00:00Z', updateError = null, raced = false) {
  const events = []; let reads = 0;
  const github = {rest: {
    actions: {
      getWorkflow: async () => ({data: {state}}),
      enableWorkflow: async () => events.push('enable'),
    },
    repos: {get: async () => ({data: {default_branch: 'main'}})},
    git: {
      getRef: async () => ({data: {object: {sha: ++reads > 1 && raced ? 'new-push' : 'old'}}}),
      getCommit: async () => ({data: {committer: {date}, tree: {sha: 'same-tree'}}}),
      createCommit: async args => {events.push(args); return {data: {sha: 'maintenance'}};},
      updateRef: async args => {events.push(args); if (updateError) throw updateError;},
    },
  }};
  return {github, context: {repo: {owner: 'owner', repo: 'repo'}}, core: {info: () => {}}, events};
}
test('manual disable is never overridden or followed by a maintenance commit', async () => {
  const m = fixture('disabled_manually'); await run(m, now); assert.deepEqual(m.events, []);
});
test('only inactivity disabling is automatically repaired', async () => {
  const m = fixture('disabled_inactivity', '2026-10-20T00:00:00Z');
  await run(m, now); assert.deepEqual(m.events, ['enable']);
  await assert.rejects(run(fixture('disabled_fork'), now), /Unexpected/);
});
test('recent activity does not create unnecessary commits', async () => {
  const m = fixture('active', '2026-10-01T00:00:00Z'); await run(m, now); assert.deepEqual(m.events, []);
});
test('maintenance preserves the tree and never force pushes', async () => {
  const m = fixture(); await run(m, now);
  assert.equal(m.events[0].tree, 'same-tree');
  assert.deepEqual(m.events[0].parents, ['old']);
  assert.equal(m.events[1].force, false);
  assert.equal(m.events[1].ref, 'heads/main');
});
test('a concurrent push is preserved while branch protection failures are reported', async () => {
  const error = Object.assign(new Error('Ref rejected'), {status: 422});
  await run(fixture('active', '2026-09-01T00:00:00Z', error, true), now);
  await assert.rejects(run(fixture('active', '2026-09-01T00:00:00Z', error), now), /Ref rejected/);
});
test('invalid dates fail visibly', async () => {
  await assert.rejects(run(fixture('active', 'invalid'), now), /Invalid commit date/);
});
