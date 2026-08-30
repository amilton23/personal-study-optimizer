import { useEffect, useMemo, useState } from "react";

const API_URL = "http://127.0.0.1:8000/api/flashcards";

function App() {
  const [topic, setTopic] = useState("");
  const [deck, setDeck] = useState(null);
  const [index, setIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [progressStep, setProgressStep] = useState(0);

  const progressMessages = [
    "Understanding your topic...",
    "Finding good study sources...",
    "Extracting key theory points...",
    "Extracting real-world examples...",
    "Turning notes into simple flashcards...",
    "Final quality check...",
  ];

  const done = !!deck && index >= deck.cards.length;
  const currentCard = useMemo(() => {
    if (!deck || done) return null;
    return deck.cards[index];
  }, [deck, done, index]);

  useEffect(() => {
    if (!loading) return;

    setProgressStep(0);
    const timer = setInterval(() => {
      setProgressStep((prev) => Math.min(prev + 1, progressMessages.length - 1));
    }, 3500);

    return () => clearInterval(timer);
  }, [loading]);

  async function generateDeck() {
    if (!topic.trim()) return;

    setLoading(true);
    setError("");
    setDeck(null);
    setIndex(0);
    setProgressStep(0);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        const payload = await response.json();
        throw new Error(payload?.detail?.message || "Failed to generate deck");
      }

      const payload = await response.json();
      setDeck(payload);
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-3xl font-bold">AI Tutor</h1>
        <p className="mt-2 text-slate-300">The flashcards generation usually takes 2 to 5 minutes to finish.</p>

        <div className="mt-6 flex gap-3">
          <input
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Type a topic"
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 outline-none focus:border-indigo-400"
          />
          <button
            onClick={generateDeck}
            disabled={loading}
            className="rounded-lg bg-indigo-500 px-5 py-3 font-semibold hover:bg-indigo-400 disabled:opacity-60"
          >
            {loading ? "Generating..." : "Start quiz"}
          </button>
        </div>

        {loading && (
          <section className="mt-4 rounded-lg border border-indigo-800 bg-indigo-950/40 p-4">
            <p className="text-indigo-200 font-medium">{progressMessages[progressStep]}</p>
            <ol className="mt-3 space-y-1 text-sm text-slate-300">
              {progressMessages.map((message, i) => (
                <li key={message}>
                  {i < progressStep ? "✅" : i === progressStep ? "⏳" : "⬜"} {message}
                </li>
              ))}
            </ol>
          </section>
        )}

        {error && <p className="mt-4 rounded bg-red-950 p-3 text-red-300">{error}</p>}

        {currentCard && (
          <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900 p-6">
            <p className="text-sm text-slate-400">Card {index + 1} / {deck.cards.length} · {currentCard.category}</p>
            <h2 className="mt-3 text-xl font-semibold">{currentCard.question}</h2>
            <p className="mt-4 text-sm text-slate-400">Source: {currentCard.source || "n/a"}</p>

            <button
              onClick={() => setIndex((v) => v + 1)}
              className="mt-6 rounded-lg bg-emerald-500 px-4 py-2 font-semibold text-slate-950 hover:bg-emerald-400"
            >
              Next question
            </button>
          </section>
        )}

        {done && (
          <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900 p-6">
            <h2 className="text-2xl font-bold">Answers</h2>
            <ol className="mt-4 space-y-3">
              {deck.cards.map((card) => (
                <li key={card.id} className="rounded-lg border border-slate-800 bg-slate-950 p-4">
                  <p className="text-sm text-slate-400">Q{card.id}: {card.question}</p>
                  <p className="mt-2">{card.answer}</p>
                </li>
              ))}
            </ol>
          </section>
        )}
      </div>
    </main>
  );
}

export default App;
