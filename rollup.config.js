import { nodeResolve } from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';

export default {
  input: 'main.ts',
  output: {
    file: 'C:/Users/rubai/Documents/Obsidian/Obsidianzk/.obsidian/plugins/sample-plugin/main.js',
    format: 'cjs'
  },
  plugins: [nodeResolve(), commonjs(), typescript()]
};
