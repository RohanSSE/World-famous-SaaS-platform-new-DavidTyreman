import { CONFIG } from "@admin/config-global";
import { SignInView } from "@admin/sections/auth";
function Page() {
  return <>
      <title>{`Sign in - ${CONFIG.appName}`}</title>

      <SignInView />
    </>;
}
export {
  Page as default
};
