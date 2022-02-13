import {
  nodeResolve
} from '@rollup/plugin-node-resolve'
import commonjs from '@rollup/plugin-commonjs';
import typescript from '@rollup/plugin-typescript';
import nodePolyfills from 'rollup-plugin-node-polyfills'
import copy from "rollup-plugin-copy-assets";

export default {
  input: 'main.ts',
  output: {
    file: './build/main.js',
    format: 'cjs',
    exports: "default"
  },
  plugins: [
    nodeResolve(),
    commonjs(),
    typescript(),
    copy({
      assets: [
        "./manifest.json",
        "./styles.css",
      ],
    }),
  ],
  external: ["obsidian", "path"]
};