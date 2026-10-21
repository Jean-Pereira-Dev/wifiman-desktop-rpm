const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const run = require('../scripts/release.cjs');
process.env.VERSION = '1.3.0';
process.env.FEDORA_VERSIONS = '["43"]';
const binary = {id: 1, name: 'wifiman-desktop-1.3.0-5.fc43.x86_64.rpm', size: 5};
const source = {id: 2, name: 'wifiman-desktop-1.3.0-5.fc43.src.rpm', size: 5};
function mock(release, assets = [], status = 404) {
  const events = [];
  const repos = {
    getReleaseByTag: async () => { if (!release) throw Object.assign(new Error('API error'), {status}); return {data: release}; },
    listReleaseAssets: () => {},
    createRelease: async args => { events.push(['create', args]); return {data: {id: 3}}; },
    deleteReleaseAsset: async args => events.push(['delete', args]),
    uploadReleaseAsset: async args => events.push(['upload', args]),
    updateRelease: async args => events.push(['publish', args]),
  };
  return {github: {rest: {repos}, paginate: async () => assets}, context: {repo: {owner: 'owner', repo: 'repo'}, sha: 'abc'}, core: {setOutput: (k,v) => events.push([k,v])}, events};
}
test('only complete published releases suppress a build', async () => {
  for (const [release, assets, expected] of [
    [null, [], 'true'], [{id: 3}, [], 'true'], [{id: 3}, [binary], 'true'],
    [{id: 3, draft: true}, [binary, source], 'true'],
    [{id: 3}, [{...binary, size: 0}, source], 'true'],
    [{id: 3}, [binary, source], 'false']]) {
    const m = mock(release, assets); await run(m, 'check');
    assert.deepEqual(m.events, [['build_required', expected]]);
  }
});
test('API errors do not masquerade as missing releases', async () => {
  await assert.rejects(run(mock(null, [], 403), 'check'), /API error/);
});
test('publish is last; retries replace matching assets', async () => {
  const previous = process.cwd(); const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'wifiman-test-'));
  try {
    process.chdir(temp); fs.mkdirSync('release-assets');
    fs.writeFileSync(path.join('release-assets', binary.name), 'rpm');
    fs.writeFileSync(path.join('release-assets', source.name), 'srpm');
    const first = mock(null); await run(first, 'publish');
    assert.equal(first.events[0][0], 'create'); assert.equal(first.events[0][1].draft, true);
    assert.equal(first.events.at(-1)[0], 'publish');
    const retry = mock({id: 3, body: 'Notes\n<!-- wifiman-copr-success -->'}, [binary, source]); await run(retry, 'publish');
    assert.deepEqual(retry.events.map(x => x[0]), ['delete', 'upload', 'delete', 'upload', 'publish']);
    assert.equal(retry.events.at(-1)[1].body, 'Notes');
    const failed = mock(null); failed.github.rest.repos.uploadReleaseAsset = async () => { throw new Error('upload failed'); };
    await assert.rejects(run(failed, 'publish'), /upload failed/);
    assert(!failed.events.some(x => x[0] === 'publish'));
  } finally { process.chdir(previous); fs.rmSync(temp, {recursive:true, force:true}); }
});
test('configured Copr must succeed before daily builds can skip', async () => {
  const marker = '<!-- wifiman-copr-success:43 -->';
  process.env.COPR_CONFIGURED = 'true';
  try {
    const pending = mock({id: 3}, [binary, source]); await run(pending, 'check');
    assert.deepEqual(pending.events, [['build_required', 'true']]);
    const done = mock({id: 3, body: marker}, [binary, source]); await run(done, 'check');
    assert.deepEqual(done.events, [['build_required', 'false']]);
    const success = mock({id: 3, body: 'Release notes'}); await run(success, 'copr-success');
    assert.equal(success.events[0][1].body, 'Release notes\n\n' + marker);
  } finally { delete process.env.COPR_CONFIGURED; }
});

test('a new stable Fedora requires new assets and a matching Copr receipt', async () => {
  process.env.FEDORA_VERSIONS = '["43","44"]';
  process.env.COPR_CONFIGURED = 'true';
  try {
    const oldAssets = mock({id: 3, body: '<!-- wifiman-copr-success:43 -->'}, [binary, source]);
    await run(oldAssets, 'check');
    assert.deepEqual(oldAssets.events, [['build_required', 'true']]);
    const assets = [binary, source, {...binary, name: binary.name.replace('fc43', 'fc44')}, {...source, name: source.name.replace('fc43', 'fc44')}];
    const pendingCopr = mock({id: 3, body: '<!-- wifiman-copr-success:43 -->'}, assets);
    await run(pendingCopr, 'check');
    assert.deepEqual(pendingCopr.events, [['build_required', 'true']]);
    const complete = mock({id: 3, body: '<!-- wifiman-copr-success:43,44 -->'}, assets);
    await run(complete, 'check');
    assert.deepEqual(complete.events, [['build_required', 'false']]);
  } finally { process.env.FEDORA_VERSIONS = '["43"]'; delete process.env.COPR_CONFIGURED; }
});
