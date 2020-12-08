import { nodeResolve } from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';

export default {
  input: 'main.ts',
  output: {
    file: 'main.js',
    format: 'cjs'
  },
  plugins: [nodeResolve(), commonjs(), typescript()]
};
