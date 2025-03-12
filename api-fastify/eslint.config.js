import globals from 'globals';
import pluginJs from '@eslint/js';
import stylisticJs from '@stylistic/eslint-plugin-js';

export default [
  {
    languageOptions: { globals: globals.node },
  },
  pluginJs.configs.recommended,
  {
    plugins: {
      '@stylistic/js': stylisticJs,
    },
    rules: {
      '@stylistic/js/comma-dangle': ['error', 'always-multiline'],
      '@stylistic/js/comma-spacing': ['error', { 'before': false, 'after': true }],
      '@stylistic/js/eol-last': ['error', 'always'],
      '@stylistic/js/indent': ['error', 2],
      '@stylistic/js/key-spacing': ['error', { 'beforeColon': false }],
      '@stylistic/js/keyword-spacing': 'error',
      '@stylistic/js/no-extra-semi': 'error',
      '@stylistic/js/no-multi-spaces': 'error',
      '@stylistic/js/no-mixed-spaces-and-tabs': 'error',
      '@stylistic/js/no-multiple-empty-lines': ['error', { max: 2 }],
      '@stylistic/js/object-curly-spacing': ['error', 'always'],
      '@stylistic/js/quotes': ['error', 'single'],
      '@stylistic/js/semi': ['error', 'always'],
    },
  },
];
