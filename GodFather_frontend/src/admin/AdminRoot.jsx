import { Outlet } from 'react-router-dom';

import '@admin/global.css';

import App from '@admin/app';
import { registerIcons } from '@admin/components/iconify/register-icons';

registerIcons();

/** Theme shell for all /admin/* routes — child routes render in <Outlet /> */
export default function AdminRoot() {
  return (
    <App>
      <Outlet />
    </App>
  );
}
