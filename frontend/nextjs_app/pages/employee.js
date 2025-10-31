// frontend/nextjs_app/pages/employee.js
import { useState } from "react";

export default function Employee() {
  const [form, setForm] = useState({ name: "", email: "", resume_text: "" });

  const register = async () => {
    const res = await fetch("/employee/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form)
    });
    const data = await res.json();
    alert("Registered: " + JSON.stringify(data));
  };

  const discover = async () => {
    const res = await fetch("/employee/discover", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: form.resume_text, k: 5 })
    });
    const data = await res.json();
    alert("Discover results: " + JSON.stringify(data));
  };

  return (
    <div style={{ padding: 24 }}>
      <h2>Employee Demo</h2>
      <div>
        <input placeholder="Name" onChange={(e)=>setForm({...form, name:e.target.value})} />
        <input placeholder="Email" onChange={(e)=>setForm({...form, email:e.target.value})} />
        <textarea placeholder="Paste resume text here" onChange={(e)=>setForm({...form, resume_text:e.target.value})} />
        <button onClick={register}>Register & Index Resume</button>
        <button onClick={discover}>Discover Jobs</button>
      </div>
    </div>
  );
}
