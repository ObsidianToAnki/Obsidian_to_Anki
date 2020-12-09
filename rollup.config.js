import { nodeResolve } from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import nodePolyfills from 'rollup-plugin-node-polyfills'

export default {
  input: 'main.ts',
  output: {
    file: 'C:/Users/rubai/Documents/Obsidian/Obsidianzk/.obsidian/plugins/sample-plugin/main.js',
    format: 'cjs',
    exports: "default"
  },
  plugins: [nodeResolve(), commonjs(), typescript()],
  external: ["obsidian", "path"]
};
