import pkg from '../package.json' with {type: 'json'};
// Shown in the footer; always matches package.json.
export const APP_VERSION: string = pkg.version;
