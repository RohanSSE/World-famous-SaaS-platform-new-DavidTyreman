import { themeConfig } from "./theme-config";
function createClasses(className) {
  return `${themeConfig.classesPrefix}__${className}`;
}
export {
  createClasses
};
