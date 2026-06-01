export function isClientUser(row) {
  return row.role === "User";
}

export function isAgencyAccount(row) {
  return row.role === "Agency";
}

/** Members — all agency-linked users (including the agency owner). */
export function isAgencyMember(row) {
  return Boolean(row.agencyId);
}

export function mapApiUser(u) {
  const roleKey = (u.role_name || "").toLowerCase();
  let role = "User";
  if (roleKey === "admin") role = "SuperAdmin";
  else if (roleKey === "agency") role = "Agency";
  else if (roleKey === "client") role = "User";

  return {
    id: u.id,
    name: u.email || "—",
    company: u.agency_name || "—",
    agencyId: u.agency ?? null,
    phone: u.phone_number || "—",
    role,
    isVerified: u.is_active === true,
    status: u.is_active === true ? "active" : "pending",
    avatarUrl: null,
    raw: u,
  };
}

export function mapApiAgency(a) {
  return {
    id: a.id,
    name: a.name || "—",
    owner_email: a.owner_email || "—",
    members_count: a.members_count ?? 0,
    sessions_count: a.sessions_count ?? 0,
    created_at: a.created_at,
    status:
      a.is_active === true && a.approved_at != null && a.approved_at !== ""
        ? "active"
        : "pending",
    raw: a,
  };
}

/** All tab: agency organizations + client users only (no agency-owner accounts). */
export function buildAllRows(users, agencies) {
  const userRows = users
    .filter(isClientUser)
    .map((u) => ({
      ...u,
      recordType: "user",
      rowKey: `user-${u.id}`,
      detail: u.company,
      info: u.role,
    }));
  const agencyRows = agencies.map((a) => ({
    ...a,
    recordType: "agency-org",
    rowKey: `agency-${a.id}`,
    detail: a.owner_email,
    info: "—",
  }));
  return [...agencyRows, ...userRows];
}

export function buildAgencyTabRows(agencies) {
  return agencies.map((a) => ({
    ...a,
    recordType: "agency-org",
    rowKey: `agency-${a.id}`,
  }));
}

export function buildMembersRows(users) {
  return users
    .filter(isAgencyMember)
    .map((u) => ({
      ...u,
      rowKey: `member-${u.id}`,
    }));
}

export function getMembersForAgency(agency, users) {
  if (!agency) return [];
  const agencyId = agency.id;
  return users.filter((u) => u.agencyId === agencyId);
}

export function countAllTab(users, agencies) {
  return agencies.length + users.filter(isClientUser).length;
}

export function countMembers(users) {
  return users.filter(isAgencyMember).length;
}
