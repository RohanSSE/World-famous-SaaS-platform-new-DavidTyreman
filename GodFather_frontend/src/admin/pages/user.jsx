import { CONFIG } from "@admin/config-global";
import { UserView } from "@admin/sections/user/view";
function Page() {
  return <>
      <title>{`Users - ${CONFIG.appName}`}</title>

      <UserView />
    </>;
}
export {
  Page as default
};
