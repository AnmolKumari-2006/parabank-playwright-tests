import { defineConfig } from "allure";

// Allure 3 with the "allure2" plugin: the classic Allure layout with a sidebar
// (Overview, Categories, Suites, Behaviors, Graphs, Timeline).
export default defineConfig({
  name: "ParaBank Test Report",
  output: "./allure-report",
  plugins: {
    allure2: {
      options: {
        reportName: "ParaBank Test Report",
        singleFile: true,
      },
    },
  },
});
