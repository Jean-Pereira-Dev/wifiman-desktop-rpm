// Called by actions/github-script. Only a complete, published release skips a build.
const fs = require('fs');
const path = require('path');
module.exports = async ({github, context, core}, mode) => {
  const version = process.env.VERSION;
  if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error('Invalid version');
  const repo = {owner: context.repo.owner, repo: context.repo.repo};
  const tag = `v${version}`;
  let release;
  try {
    release = (await github.rest.repos.getReleaseByTag({...repo, tag})).data;
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  const coprMarker = '<!-- wifiman-copr-success -->';
  if (mode === 'copr-success') {
    if (!release) throw new Error('Cannot record Copr success without a release');
    await github.rest.repos.updateRelease({...repo, release_id: release.id,
      body: `${(release.body || '').replace(coprMarker, '').trim()}\n\n${coprMarker}`});
    return;
  }
  if (mode === 'check') {
    const assets = release ? await github.paginate(github.rest.repos.listReleaseAssets,
      {...repo, release_id: release.id, per_page: 100}) : [];
    const complete = release && !release.draft && !release.prerelease &&
      assets.some(a => a.size > 0 && a.name.startsWith(`wifiman-desktop-${version}-`) && a.name.endsWith('.fc43.x86_64.rpm')) &&
      assets.some(a => a.size > 0 && a.name.startsWith(`wifiman-desktop-${version}-`) && a.name.endsWith('.src.rpm')) &&
      (process.env.COPR_CONFIGURED !== 'true' || (release.body || '').includes(coprMarker));
    core.setOutput('build_required', String(!complete));
    return;
  }
  const files = fs.readdirSync('release-assets').filter(f => f.endsWith('.rpm'));
  if (!files.some(f => f.endsWith('.src.rpm')) || !files.some(f => f.endsWith('.fc43.x86_64.rpm')))
    throw new Error('Missing tested RPM or SRPM');
  if (!release) release = (await github.rest.repos.createRelease({...repo,
    tag_name: tag, target_commitish: context.sha, name: `wifiman-desktop ${version}`,
    body: `Fedora 43 RPM and SRPM built from the official WiFiman Desktop ${version} package.`,
    draft: true, prerelease: false})).data;
  const assets = await github.paginate(github.rest.repos.listReleaseAssets,
    {...repo, release_id: release.id, per_page: 100});
  for (const file of files) {
    const existing = assets.find(a => a.name === file);
    if (existing) await github.rest.repos.deleteReleaseAsset({...repo, asset_id: existing.id});
    await github.rest.repos.uploadReleaseAsset({...repo, release_id: release.id,
      name: file, data: fs.readFileSync(path.join('release-assets', file))});
  }
  await github.rest.repos.updateRelease({...repo, release_id: release.id, draft: false,
    body: (release.body || '').replace(coprMarker, '').trim()});
};
