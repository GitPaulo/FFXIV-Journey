import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';
import viteCompression from 'vite-plugin-compression';

export default defineConfig({
	plugins: [
		sveltekit(),
		viteCompression({
			algorithm: 'gzip',
			ext: '.gz',
			threshold: 1024, // Only compress files larger than 1KB
			filter: /\.(json|svg)$/, // Mostly compress JSON and SVG files
		}),
	]
});
