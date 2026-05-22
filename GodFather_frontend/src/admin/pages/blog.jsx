import { _posts } from "@admin/_mock";
import { CONFIG } from "@admin/config-global";
import { BlogView } from "@admin/sections/blog/view";
function Page() {
  return <>
      <title>{`Blog - ${CONFIG.appName}`}</title>

      <BlogView posts={_posts} />
    </>;
}
export {
  Page as default
};
