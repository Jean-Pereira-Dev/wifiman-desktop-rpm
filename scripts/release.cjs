// Called by actions/github-script. Only a complete, published release skips a build.
const fs = require('fs');
const path = require('path');
module.exports = async ({github, context, core}, mode) => {
  const version = process.env.VERSION;
  if (!/^\d+\.\d+\.\d+$/.test(version)) throw new Error('Invalid version');
  const targets = JSON.parse(process.env.FEDORA_VERSIONS || '[]');
  if (!Array.isArray(targets) || !targets.length || targets.some(v => !/^[1-9][0-9]*$/.test(v)))
    throw new Error('Invalid Fedora target list');
  const versions = [...new Set(targets.map(String))].sort((a, b) => Number(a) - Number(b));
  const distTags = versions.map(v => `fc${v}`);
  if (process.env.EPEL_VERSION === '10') distTags.push('el10');
  const suseTags = JSON.parse(process.env.OPENSUSE_DIST_TAGS || '[]');
  if (!Array.isArray(suseTags) || suseTags.some(v => !['suse1600', 'suse1699'].includes(v)))
    throw new Error('Invalid openSUSE targets');
  distTags.push(...new Set(suseTags));
  const completeFiles = files => distTags.every(v =>
    files.some(f => f.startsWith(`wifiman-desktop-${version}-`) && f.endsWith(`.${v}.x86_64.rpm`)) &&
    files.some(f => f.startsWith(`wifiman-desktop-${version}-`) && f.endsWith(`.${v}.src.rpm`)));
  const clearCoprMarker = body => (body || '').replace(/<!-- wifiman-copr-success(?::[a-z0-9,]+)? -->/g, '').trim();
  const releaseIntro = `Fedora ${versions.join(', ')} RPMs and SRPMs${process.env.EPEL_VERSION === '10' ? ' plus Enterprise Linux 10 packages' : ''}${suseTags.length ? ' plus openSUSE packages' : ''} built from the official WiFiman Desktop ${version} package.`;
  const repo = {owner: context.repo.owner, repo: context.repo.repo};
  const tag = `v${version}`;
  let release;
  try {
    release = (await github.rest.repos.getReleaseByTag({...repo, tag})).data;
  } catch (error) {
    if (error.status !== 404) throw error;
  }
  const coprMarker = `<!-- wifiman-copr-success:${versions.join(',')}${process.env.EPEL_VERSION === '10' ? ',epel10' : ''}${suseTags.length ? ',' + [...new Set(suseTags)].sort().join(',') : ''} -->`;
  if (mode === 'copr-success') {
    if (!release) throw new Error('Cannot record Copr success without a release');
    await github.rest.repos.updateRelease({...repo, release_id: release.id,
      body: `${clearCoprMarker(release.body)}\n\n${coprMarker}`});
    return;
  }
  if (mode === 'check') {
    const assets = release ? await github.paginate(github.rest.repos.listReleaseAssets,
      {...repo, release_id: release.id, per_page: 100}) : [];
    const complete = release && !release.draft && !release.prerelease &&
      completeFiles(assets.filter(a => a.size > 0).map(a => a.name)) &&
      (process.env.COPR_CONFIGURED !== 'true' || (release.body || '').includes(coprMarker));
    core.setOutput('build_required', String(!complete));
    return;
  }
  const files = fs.readdirSync('release-assets').filter(f => f.endsWith('.rpm'));
  if (!completeFiles(files))
    throw new Error('Missing tested RPM or SRPM');
  if (!release) release = (await github.rest.repos.createRelease({...repo,
    tag_name: tag, target_commitish: context.sha, name: `wifiman-desktop ${version}`,
    body: releaseIntro,
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
    body: clearCoprMarker(release.body).replace(/^Fedora [\d, ]+ RPMs? and SRPMs?(?: plus Enterprise Linux 10 packages)?(?: plus openSUSE packages)? built from the official WiFiman Desktop [\d.]+ package\./, releaseIntro)});
};
