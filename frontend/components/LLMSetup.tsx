import type { LLMStatus } from "@/types/live";

export function LLMSetup({status}: {status?: LLMStatus}) {
  return <details className="trip-notes">
    <summary>Assistant setup · {status?.label ?? "Local or Gemini"}</summary>
    <p className="mt-3">Choose a local model or Google Gemini in the backend <code>.env</code> file, then restart the backend and reload this page.</p>
    <p className="mt-3"><strong>To use Gemini</strong>, add your API key and a model identifier available to your key:</p>
    <pre className="my-3 overflow-x-auto rounded-lg bg-slate-100 p-3 text-xs">{"LLM_PROVIDER=gemini\nGEMINI_API_KEY=your-key\nGEMINI_MODEL=your-model-identifier"}</pre>
    <p>Gemini sends your message, recent conversation, and relevant trip context to Google. The API key stays on the backend. Keep it out of chat messages and Git.</p>
    <p className="mt-3">Get a key from <a className="underline" href="https://aistudio.google.com/apikey" target="_blank" rel="noreferrer">Google AI Studio</a>. To use local inference, set <code>LLM_PROVIDER=local</code> and configure <code>LOCAL_LLM_MODEL</code> and <code>LOCAL_LLM_BASE_URL</code>. The trip form works with either assistant unavailable.</p>
  </details>;
}
