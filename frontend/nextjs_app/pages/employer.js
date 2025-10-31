// frontend/nextjs_app/pages/employer.js
import { useState } from "react";
import useSWR from "swr";
const fetcher = (url) => fetch(url).then((r) => r.json());

export default function Employer() {
  const [form, setForm] = useState({ name: "", email: "", title: "", description: "" });
  const BACKEND = "http://127.0.0.1:8000";

  const createEmployer = async () => {
    const res = await fetch(`${BACKEND}/api/employer/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: form.name, email: form.email, profile: "" })
    });
    const data = await res.json();
    alert("Employer created: " + JSON.stringify(data));
  };

  const postJob = async () => {
    const res = await fetch(`${BACKEND}/api/employer/post_job`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ employer_id: 1, title: form.title, description: form.description })
    });
    const data = await res.json();
    alert("Job posted: " + JSON.stringify(data));
  };
  return (
    <div style={{ padding: 24 }}>
      <h2>Employer Demo</h2>
      <div>
        <h3>Create Employer</h3>
        <input placeholder="Name" onChange={(e)=>setForm({...form, name:e.target.value})} />
        <input placeholder="Email" onChange={(e)=>setForm({...form, email:e.target.value})} />
        <button onClick={createEmployer}>Create</button>
      </div>
      <div style={{ marginTop: 24 }}>
        <h3>Post Job</h3>
        <input placeholder="Title" onChange={(e)=>setForm({...form, title:e.target.value})} />
        <textarea placeholder="Description" onChange={(e)=>setForm({...form, description:e.target.value})} />
        <button onClick={postJob}>Post Job</button>
      </div>
    </div>
  );
}
