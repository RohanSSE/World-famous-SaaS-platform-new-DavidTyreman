import { useEffect, useState } from "react";
import Typography from "@mui/material/Typography";
import Card from "@mui/material/Card";
import Alert from "@mui/material/Alert";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import { DashboardContent } from "@admin/layouts/dashboard/content";
import adminApi from "@admin/lib/adminApi";

export default function ReviewDashboardPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    adminApi
      .feedbackReview(60)
      .then((d) => setItems(d.items || []))
      .catch((e) => setError(e.response?.data?.detail || e.message));
  }, []);

  return (
    <DashboardContent maxWidth="xl">
      <Typography variant="h4" sx={{ mb: 2 }}>
        Feedback & export review
      </Typography>
      {error && <Alert severity="warning">{error}</Alert>}
      <Card sx={{ p: 2, mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Session</TableCell>
              <TableCell>Key</TableCell>
              <TableCell>Preview</TableCell>
              <TableCell>Updated</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((row, i) => (
              <TableRow key={`${row.session_id}-${row.key}-${i}`}>
                <TableCell>{row.session_id}</TableCell>
                <TableCell>{row.key}</TableCell>
                <TableCell sx={{ maxWidth: 400 }}>{row.preview}</TableCell>
                <TableCell>{row.updated_at}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </DashboardContent>
  );
}
