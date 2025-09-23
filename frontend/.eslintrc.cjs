// .eslintrc.cjs
module.exports = {
    root: true,
    parser: '@typescript-eslint/parser',
    plugins: ['@typescript-eslint', 'react', 'react-native'],
    extends: [
		'plugin:react/recommended',
		'plugin:react-native/all',
		'plugin:react-hooks/recommended'
	],
    settings: { react: { version: 'detect' } },
    rules: {
        'react-native/no-raw-text': ['error', { skip: ['Trans', 'Icon'] }],
        'react/react-in-jsx-scope': 'off',
    },
};