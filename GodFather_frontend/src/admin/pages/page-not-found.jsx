import { CONFIG } from "@admin/config-global";
import { NotFoundView } from "@admin/sections/error";
function Page() {
  return <>
      <title>{`404 page not found! | Error - ${CONFIG.appName}`}</title>

      <NotFoundView />
    </>;
}
export {
  Page as default
};
