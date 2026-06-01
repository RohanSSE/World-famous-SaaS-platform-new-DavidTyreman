function DashboardContent({ children, className = "", ...other }) {
  return (
    <div className={`admin-adb-content ${className}`.trim()} {...other}>
      {children}
    </div>
  );
}

export { DashboardContent };
