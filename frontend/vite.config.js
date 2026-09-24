import { defineConfig, loadEnv } from 'vite';
import vue from '@vitejs/plugin-vue';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), '');
    return {
        base: env.VITE_BASE_PATH || '/',
        plugins: [vue(), tailwindcss()],
        test: { environment: 'jsdom' },
    };
});
