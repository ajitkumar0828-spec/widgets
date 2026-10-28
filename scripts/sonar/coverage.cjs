/* Separate Jest processes avoid shared mutable package configs and LCOV collisions. */
const {spawnSync} = require('node:child_process');
const {mkdirSync, writeFileSync, rmSync, existsSync} = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const packages = [
  ['ai-assistant', '@webex/cc-ai-assistant'],
  ['cc-components', '@webex/cc-components'],
  ['cc-digital-channels', '@webex/cc-digital-channels'],
  ['station-login', '@webex/cc-station-login'],
  ['store', '@webex/cc-store'],
  ['task', '@webex/cc-task'],
  ['ui-logging', '@webex/cc-ui-logging'],
  ['user-state', '@webex/cc-user-state'],
];
mkdirSync(path.join(root, 'reports/sonar/jest'), {recursive: true});
const statuses = [];
for (const [directory, workspace] of packages) {
  const coverage = path.join(root, 'coverage/sonar', directory);
  rmSync(coverage, {recursive: true, force: true});
  const jestArgs = [
    '--runInBand', '--coverage', '--coverageReporters=lcov', '--coverageReporters=json-summary',
    '--coverageDirectory=' + coverage,
    '--collectCoverageFrom=packages/contact-center/' + directory + '/src/**/*.{js,jsx,ts,tsx}',
    '--collectCoverageFrom=!**/*.d.ts',
    '--json', '--outputFile=' + path.join(root, 'reports/sonar/jest', directory + '.json'),
  ];
  const yarnArgs = ['.yarn/releases/yarn-4.5.1.cjs', 'workspace', workspace];
  const options = {cwd: root, stdio: 'inherit', env: {...process.env, NODE_ENV: 'test'}};
  const result = spawnSync(process.execPath, [...yarnArgs, 'test:unit', ...jestArgs], options);
  let coverageOnly = null;
  const pkg = require(path.join(root, 'packages/contact-center', directory, 'package.json'));
  if (result.status !== 0 && pkg.scripts['test:unit'].startsWith('tsc ') &&
      !existsSync(path.join(coverage, 'lcov.info'))) {
    // The original tsc && jest command failed before Jest. Keep its failure;
    // run the same package Jest config separately solely to produce coverage.
    coverageOnly = spawnSync(process.execPath, [...yarnArgs, 'exec', 'jest', ...jestArgs], options).status;
  }
  statuses.push({workspace, exitCode: result.status, coverageOnlyJestExitCode: coverageOnly, signal: result.signal,
    status: result.status === 0 ? 'passed' : 'failed'});
  writeFileSync(path.join(root, 'reports/sonar/test-status.json'), JSON.stringify(statuses, null, 2) + '\n');
}
statuses.push({workspace: '@webex/cc-widgets', status: 'no tests; production code stays in analysis'});
writeFileSync(path.join(root, 'reports/sonar/test-status.json'), JSON.stringify(statuses, null, 2) + '\n');
process.exitCode = statuses.some(s => s.status === 'failed') ? 1 : 0;
