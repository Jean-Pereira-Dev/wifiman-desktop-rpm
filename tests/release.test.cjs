const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('fs');
const os = require('os');
const path = require('path');
const run = require('../scripts/release.cjs');
process.env.VERSION = '1.3.0';
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
    const retry = mock({id: 3}, [binary, source]); await run(retry, 'publish');
    assert.deepEqual(retry.events.map(x => x[0]), ['delete', 'upload', 'delete', 'upload', 'publish']);
    const failed = mock(null); failed.github.rest.repos.uploadReleaseAsset = async () => { throw new Error('upload failed'); };
    await assert.rejects(run(failed, 'publish'), /upload failed/);
    assert(!failed.events.some(x => x[0] === 'publish'));
  } finally { process.chdir(previous); fs.rmSync(temp, {recursive:true, force:true}); }
});
