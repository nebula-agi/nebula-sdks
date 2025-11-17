"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tsup_1 = require("tsup");
exports.default = (0, tsup_1.defineConfig)({
    entry: ['src/index.ts'],
    format: ['cjs', 'esm'],
    dts: true,
    splitting: false,
    sourcemap: true,
    clean: true,
    minify: false,
    treeshake: true,
    external: [],
    target: 'es2020',
    outDir: 'dist',
    onSuccess: 'echo "Build completed successfully!"',
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoidHN1cC5jb25maWcuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyJ0c3VwLmNvbmZpZy50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOztBQUFBLCtCQUFvQztBQUVwQyxrQkFBZSxJQUFBLG1CQUFZLEVBQUM7SUFDMUIsS0FBSyxFQUFFLENBQUMsY0FBYyxDQUFDO0lBQ3ZCLE1BQU0sRUFBRSxDQUFDLEtBQUssRUFBRSxLQUFLLENBQUM7SUFDdEIsR0FBRyxFQUFFLElBQUk7SUFDVCxTQUFTLEVBQUUsS0FBSztJQUNoQixTQUFTLEVBQUUsSUFBSTtJQUNmLEtBQUssRUFBRSxJQUFJO0lBQ1gsTUFBTSxFQUFFLEtBQUs7SUFDYixTQUFTLEVBQUUsSUFBSTtJQUNmLFFBQVEsRUFBRSxFQUFFO0lBQ1osTUFBTSxFQUFFLFFBQVE7SUFDaEIsTUFBTSxFQUFFLE1BQU07SUFDZCxTQUFTLEVBQUUsc0NBQXNDO0NBQ2xELENBQUMsQ0FBQyIsInNvdXJjZXNDb250ZW50IjpbImltcG9ydCB7IGRlZmluZUNvbmZpZyB9IGZyb20gJ3RzdXAnO1xuXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoe1xuICBlbnRyeTogWydzcmMvaW5kZXgudHMnXSxcbiAgZm9ybWF0OiBbJ2NqcycsICdlc20nXSxcbiAgZHRzOiB0cnVlLFxuICBzcGxpdHRpbmc6IGZhbHNlLFxuICBzb3VyY2VtYXA6IHRydWUsXG4gIGNsZWFuOiB0cnVlLFxuICBtaW5pZnk6IGZhbHNlLFxuICB0cmVlc2hha2U6IHRydWUsXG4gIGV4dGVybmFsOiBbXSxcbiAgdGFyZ2V0OiAnZXMyMDIwJyxcbiAgb3V0RGlyOiAnZGlzdCcsXG4gIG9uU3VjY2VzczogJ2VjaG8gXCJCdWlsZCBjb21wbGV0ZWQgc3VjY2Vzc2Z1bGx5IVwiJyxcbn0pO1xuXG5cblxuXG4iXX0=