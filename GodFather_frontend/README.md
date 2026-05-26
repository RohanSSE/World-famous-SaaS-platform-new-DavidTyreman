# Godfather Frontend

Single React app — one `src`, one port (**4001**).

## Structure

```
GodFather_frontend/
├── src/
│   ├── pages/          # Main app (user, agency, manifesto)
│   └── admin/          # Super Admin panel (MUI) — routes under /admin
└── public/assets/      # Admin UI images/icons
```

**Note:** The old duplicate `admin/` folder at the repo root has been removed. All admin UI code lives in `src/admin/` only.

Backend Django admin (database) stays at `GodFather_backend` → `http://127.0.0.1:8000/admin/` (use `createsuperuser`).

## URLs

| URL | Description |
|-----|-------------|
| `http://localhost:4001/` | Main app |
| `http://localhost:4001/admin/sign-in` | Super Admin sign-in |
| `http://localhost:4001/admin/` | Admin dashboard (after login) |
| `http://localhost:4001/admin/user` | Users table |

## Run

```bash
npm install
npm run dev
```

Sign-in accepts any email + password (demo auth in `localStorage` until API is wired).
