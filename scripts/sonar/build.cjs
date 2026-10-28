/* Build only Contact Center packages and their shared unit-test dependency. */
const {spawnSync} = require('node:child_process');
const {mkdirSync, writeFileSync} = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const statuses = [];
mkdirSync(path.join(root, 'reports/sonar'), {recursive: true});
function yarn(...args) {
  const result = spawnSync(process.execPath, ['.yarn/releases/yarn-4.5.1.cjs', ...args], {
    cwd: root, stdio: 'inherit', env: {...process.env, NODE_ENV: 'development'},
  });
  statuses.push({command: ['yarn', ...args].join(' '), exitCode: result.status,
    signal: result.signal, status: result.status === 0 ? 'passed' : 'failed'});
  writeFileSync(path.join(root, 'reports/sonar/build-status.json'), JSON.stringify(statuses, null, 2) + '\n');
}
yarn('workspace', '@webex/cc-store', 'build:src');
// Store's webpack uses transpileOnly, so generate declarations for dependent unit tests.
yarn('workspace', '@webex/cc-store', 'exec', 'tsc', '--emitDeclarationOnly');
yarn('workspace', '@webex/cc-ui-logging', 'build:src');
// Its package.json resolves dist/index.d.ts, whereas webpack emits dist/types/index.d.ts.
yarn('workspace', '@webex/cc-ui-logging', 'exec', 'tsc', '--emitDeclarationOnly', '--declarationDir', 'dist');
for (const workspace of [
  '@webex/cc-components', '@webex/test-fixtures', '@webex/cc-station-login',
  '@webex/cc-user-state', '@webex/cc-task', '@webex/cc-digital-channels',
  '@webex/cc-ai-assistant', '@webex/cc-widgets',
]) yarn('workspace', workspace, 'build:src');

process.exitCode = statuses.some(s => s.status === 'failed') ? 1 : 0;
