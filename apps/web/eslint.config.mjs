import js from "@eslint/js";

export default [
  {
    ignores: [
      ".next/**",
      "**/.next/**",
      "node_modules/**",
      "**/node_modules/**",
      "build/**",
      "dist/**",
      "coverage/**",
      "**/*.ts",
      "**/*.tsx",
    ],
  },
  js.configs.recommended,
  {
    files: ["**/*.js", "**/*.mjs"],
    rules: {
      "no-unused-vars": "off",
      "no-undef": "off",
    },
  },
];
