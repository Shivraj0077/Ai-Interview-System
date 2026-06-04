import fetch from "node-fetch";
import { createClient } from "@supabase/supabase-js";
import { GoogleGenerativeAI } from "@google/generative-ai";

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLUC_SUPABASE_ANON_KEY
);

export async function POST(req) {
  const { query } = await req.json();

  // 1. embedding from MiniLM service
  const embRes = await fetch("http://localhost:8000/embed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texts: [query] })
  });

  const embData = await embRes.json();
  const queryEmbedding = embData.embeddings[0];

  // 2. retrieve context
  const { data } = await supabase.rpc("match_documents", {
    query_embedding: queryEmbedding,
    match_count: 3
  });

  const context = data.map(d => d.content).join("\n");

  // 3. Gemini generation
  const model = genAI.getGenerativeModel({ model: "gemini-3-flash-preview" });

  const result = await model.generateContent(
    `Answer only using the context below.\n\nContext:\n${context}\n\nQuestion:\n${query}`
  );

  const response = result.response.text();

  return Response.json({ answer: response });
}