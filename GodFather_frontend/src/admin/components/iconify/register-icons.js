import { addCollection } from "@iconify/react";
import allIcons from "./icon-sets";
const iconSets = Object.entries(allIcons).reduce((acc, [key, value]) => {
  const [prefix, iconName] = key.split(":");
  const existingPrefix = acc.find((item) => item.prefix === prefix);
  if (existingPrefix) {
    existingPrefix.icons[iconName] = value;
  } else {
    acc.push({
      prefix,
      icons: {
        [iconName]: value
      }
    });
  }
  return acc;
}, []);
const allIconNames = Object.keys(allIcons);
let areIconsRegistered = false;
function registerIcons() {
  if (areIconsRegistered) {
    return;
  }
  iconSets.forEach((iconSet) => {
    const iconSetConfig = {
      ...iconSet,
      width: iconSet.prefix === "carbon" && 32 || 24,
      height: iconSet.prefix === "carbon" && 32 || 24
    };
    addCollection(iconSetConfig);
  });
  areIconsRegistered = true;
}
export {
  allIconNames,
  iconSets,
  registerIcons
};
