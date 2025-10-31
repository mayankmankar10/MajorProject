// frontend/nextjs_app/pages/index.js
import Link from "next/link";

export default function Home() {
  return (
    <div style={{ padding: 32 }}>
      <h1>Manpower Connector</h1>
      <p>Demo frontend for Employer & Employee flows</p>
      <ul>
        <li><Link href="/employer">Employer Dashboard</Link></li>
        <li><Link href="/employee">Employee Dashboard</Link></li>
      </ul>
    </div>
  );
}
