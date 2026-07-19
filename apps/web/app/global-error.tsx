"use client";

// Backstop for errors in the root layout itself. Must define its own <html>/<body>
// because it replaces the root layout when active. Inline styles only (globals may
// not have loaded).
export default function GlobalError() {
  return (
    <html lang="te">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "12px",
          textAlign: "center",
          padding: "2rem",
          color: "#1c1917",
          background: "#f4f2ec",
        }}
      >
        <p style={{ fontSize: "2rem" }}>🌾</p>
        <p style={{ fontWeight: 600 }}>ఏదో తప్పు జరిగింది · Something went wrong</p>
        <button
          onClick={() => window.location.reload()}
          style={{
            marginTop: "8px",
            borderRadius: "16px",
            background: "#15803d",
            color: "#fff",
            fontWeight: 600,
            padding: "10px 20px",
            border: "none",
          }}
        >
          మళ్లీ ప్రయత్నించండి · Retry
        </button>
      </body>
    </html>
  );
}
