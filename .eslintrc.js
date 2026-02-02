module.exports = {
  root: true,
  extends: ['next/core-web-vitals', 'prettier'],
  rules: {
    'prefer-const': 'error',
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
  },
};
