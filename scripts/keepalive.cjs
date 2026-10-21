// Keep scheduled checks active without overriding a manual workflow disable.
module.exports = async ({github, context, core}, now = new Date()) => {
  const repo = {owner: context.repo.owner, repo: context.repo.repo};
  const workflow = (await github.rest.actions.getWorkflow({...repo, workflow_id: 'build-and-test.yml'})).data;
  if (workflow.state === 'disabled_manually') {
    core.info('Build workflow manually disabled; leaving it disabled.');
    return;
  }
  if (workflow.state === 'disabled_inactivity') {
    await github.rest.actions.enableWorkflow({...repo, workflow_id: 'build-and-test.yml'});
    core.info('Re-enabled build workflow after GitHub inactivity disabling.');
  } else if (workflow.state !== 'active') {
    throw new Error(`Unexpected build workflow state: ${workflow.state}`);
  }
  const branch = (await github.rest.repos.get(repo)).data.default_branch;
  const ref = (await github.rest.git.getRef({...repo, ref: `heads/${branch}`})).data;
  const head = (await github.rest.git.getCommit({...repo, commit_sha: ref.object.sha})).data;
  const committed = new Date(head.committer.date);
  if (!Number.isFinite(committed.getTime())) throw new Error('Invalid commit date');
  if (now - committed < 30 * 86400 * 1000) {
    core.info('Repository has recent activity; no maintenance commit needed.');
    return;
  }
  const commit = (await github.rest.git.createCommit({...repo,
    message: 'Keep daily release checks active [skip ci]',
    tree: head.tree.sha, parents: [ref.object.sha],
    author: {name: 'github-actions[bot]', email: '41898282+github-actions[bot]@users.noreply.github.com'},
  })).data;
  try {
    await github.rest.git.updateRef({...repo, ref: `heads/${branch}`, sha: commit.sha, force: false});
  } catch (error) {
    // A concurrent push is already fresh activity. Never overwrite that push.
    if (error.status !== 422) throw error;
    const current = (await github.rest.git.getRef({...repo, ref: `heads/${branch}`})).data;
    if (current.object.sha === ref.object.sha) throw error;
    core.info('A concurrent push refreshed repository activity; leaving it intact.');
  }
};
