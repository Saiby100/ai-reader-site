import { google } from "@ai-sdk/google";
import { streamText } from "ai";

export async function POST(req: Request) {
  const { messages, context } = await req.json();

  const system = context
    ? `You are a reading assistant. The user is currently reading the following text. Answer their questions based on this context. Be concise and helpful.

--- CURRENT READING CONTEXT ---
${context}
--- END CONTEXT ---`
    : "You are a reading assistant. Help the user understand what they are reading. Be concise and helpful.";

  const result = streamText({
    model: google("gemini-2.0-flash"),
    system,
    messages,
  });

  return result.toUIMessageStreamResponse();
}
