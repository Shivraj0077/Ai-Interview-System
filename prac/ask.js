import fetch from "node-fetch";
import { createClient } from "@supabase/supabase-js";
import { GoogleGenerativeAI } from "@google/generative-ai";
import * as dotenv from 'dotenv';
dotenv.config();

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

const supabase = createClient(
  process.env.SUPABASE_URL || process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.SUPABASE_KEY || process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
);

async function ask(query) {
  console.log(`\n🔍 Searching documents for: "${query}"...`);

  // 1. embedding from MiniLM service
  const embRes = await fetch("http://localhost:8000/embed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texts: [query] })
  });

  const embData = await embRes.json();
  const queryEmbedding = embData.embeddings[0];

  // 2. retrieve context
  const { data, error } = await supabase.rpc("match_documents", {
    query_embedding: queryEmbedding,
    match_count: 3
  });

  if (error) {
    console.error("❌ RPC Error:", error);
    return;
  }

  if (!data || data.length === 0) {
    console.log("⚠️ No relevant documents found in Supabase. Did you run ingest.js?");
    return;
  }

  const context = data.map(d => d.content).join("\n");
  console.log("📝 Context retrieved from DB:\n", context, "\n");

  // 3. Gemini generation (Make sure you use the right model string like 'gemini-1.5-flash')
  console.log("🧠 Sending to Gemini...");
  const model = genAI.getGenerativeModel({ model: "gemini-3-flash-preview" });

  const result = await model.generateContent(
    `Answer only using the context below.\n\nContext:\n${context}\n\nQuestion:\n${query}`
  );

  console.log("\n💡 Answer:");
  console.log(result.response.text());
}

// Read the question from the terminal command arguments
const question = process.argv[2] || "What is RAG?";
ask(question);
