// frontend/nextjs_app/pages/employer.js
import { useState } from "react";
import useSWR from "swr";
const fetcher = (url) => fetch(url).then((r) => r.json());

export default function Employer() {
  const [form, setForm] = useState({ name: "", email: "", title: "", description: "" });
  const createEmployer = async () => {
    await fetch("/api/employer/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: form.name, email: form.email, profile: "" })
    });
    alert("Employer created");
  };
  const postJob = async () => {
    await fetch("/employer/post_job", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ employer_id: 1, title: form.title, description: form.description })
    });
    alert("Job posted (dev endpoint)");
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
