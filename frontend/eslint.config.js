// eslint.config.js
import expo from 'eslint-config-expo';

export default [
  ...expo,
  {
    settings: {
      'import/resolver': {
        node: {
          extensions: [
            '.js', '.jsx', '.ts', '.tsx', '.json',
            '.png', '.jpg', '.jpeg', '.gif'
          ],
        },
      },
    },
  },
];