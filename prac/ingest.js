import fetch from "node-fetch";
import { createClient } from "@supabase/supabase-js";
import * as dotenv from 'dotenv';
dotenv.config();

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY
);

const documents = [
  "RAG stands for Retrieval Augmented Generation",
  "MiniLM is a lightweight embedding model"
];

async function ingest() {
  // call embedding service
  const res = await fetch("http://localhost:8000/embed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texts: documents })
  });

  const data = await res.json();

  // store in DB
  for (let i = 0; i < documents.length; i++) {
    const { data: insertData, error } = await supabase.from("documents").insert({
      content: documents[i],
      embeddings: data.embeddings[i]
    });
    
    if (error) {
      console.error(`❌ Error inserting document ${i}:`, error.message);
    } else {
      console.log(`✅ Successfully inserted document ${i}`);
    }
  }
}

ingest();
