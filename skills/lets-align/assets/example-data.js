// Example data file for review.html (lets-align skill). Copy it to data/current.js next to the page,
// then replace the content. Schema and rules: references/schema.md. Check it: node scripts/check.mjs <file>
{
  // A small helper for pictures. Visuals are plain HTML; the page styles .nv (a row), .pill, and .sw (a swatch).
  const screen = (parts) =>
    `<span class="nv">${parts.map((p) => (p.startsWith("*") ? `<span class="pill">${p.slice(1)}</span>` : `<span>${p}</span>`)).join("")}</span>`;

  window.REVIEW = {
    id: "notes-app-sign-in",
    title: "Notes app · sign-in review",
    source: "PLAN.md (open decisions 1–6)",
    context:
      "A small notes web app. The plan is written. These are the choices the sign-in work needs from the owner before the build starts.",
    // accent: "#1F6FEB",   // the project's brand color, if it has one; the page defaults to violet
    rounds: [
      {
        id: "now",
        title: "Round 1: before we build sign-in",
        needed_by: "the sign-in build",
        status: "open",
        groups: [
          {
            id: "method",
            title: "How people sign in",
            items: [
              {
                id: "D1",
                title: "Sign-in method",
                rec: 0,
                q: "How should people sign in?",
                why: "Most visitors will come from a phone.",
                options: [
                  {
                    label: "A link sent by email",
                    pro: "No password to forget.",
                    con: "People must open their email each time they sign in on a new device.",
                  },
                  {
                    label: "Email and password",
                    pro: "Familiar to everyone.",
                    con: "We must build password reset, and weak passwords are a risk.",
                  },
                  {
                    label: "Google account",
                    pro: "One tap for most people.",
                    con: "People without a Google account cannot sign in.",
                  },
                ],
              },
              {
                id: "D2",
                title: "First screen",
                rec: 0,
                q: "What should people see right after they sign in?",
                options: [
                  {
                    label: "Their latest note",
                    pro: "They continue where they stopped.",
                    visual: screen([
                      "☰",
                      "Shopping list (edited today)",
                      "*New note",
                    ]),
                  },
                  {
                    label: "A list of all notes",
                    pro: "Easy to find an old note.",
                    con: "One more tap to open a note.",
                    visual: screen([
                      "☰",
                      "All notes (24)",
                      "Search",
                      "*New note",
                    ]),
                  },
                ],
              },
              {
                id: "D3",
                title: "Stay signed in",
                rec: 1,
                q: "How long should people stay signed in on their own device?",
                example:
                  "With 30 days, a person who signs in today must sign in again next month.",
                options: [
                  {
                    label: "1 day",
                    pro: "Safer on shared computers.",
                    con: "People sign in almost every day.",
                  },
                  {
                    label: "30 days",
                    pro: "Few sign-ins, and still safe enough for notes.",
                    con: "A lost phone stays signed in for up to a month.",
                  },
                ],
              },
            ],
          },
          {
            id: "data",
            title: "Data",
            items: [
              {
                id: "D4",
                title: "Import from other apps",
                multi: true,
                q: "Which apps should people be able to import notes from?",
                options: [
                  { label: "Plain text files", pro: "Works for everyone." },
                  { label: "Markdown files", pro: "Keeps headings and lists." },
                  {
                    label: "Another notes app export",
                    con: "Each app has its own format, so each one is extra work.",
                  },
                ],
              },
              {
                id: "D5",
                title: "Brand name",
                q: "What is the final name of the app, as people will see it on the sign-in screen?",
                options: [],
              },
            ],
          },
          {
            id: "defaults",
            title: "Claude’s picks",
            defaults: true,
            intro:
              "Small choices. I picked a safe answer for each one. Accept all with one click, or open one to change it.",
            items: [
              {
                id: "D6",
                title: "Error messages",
                rec: 0,
                q: "How should error messages sound?",
                options: [
                  { label: "Short and plain", pro: "Easy to read on a phone." },
                  {
                    label: "Friendly and longer",
                    con: "Takes more space on small screens.",
                  },
                ],
              },
              {
                id: "D7",
                title: "Sign-out button",
                rec: 0,
                q: "Where should the sign-out button be?",
                options: [
                  {
                    label: "In the menu",
                    pro: "Out of the way, and easy to find.",
                    visual: screen(["☰ → Settings, Sign out"]),
                  },
                  {
                    label: "On every screen",
                    con: "Takes space, and people press it by mistake.",
                    visual: screen(["Notes", "*Sign out"]),
                  },
                ],
              },
            ],
          },
        ],
      },
      {
        id: "launch",
        title: "Round 2: before launch",
        needed_by: "launch",
        status: "closed",
        groups: [
          {
            id: "launch",
            title: "Launch",
            items: [
              {
                id: "L1",
                title: "Analytics",
                q: "Do we count visits, and with which tool?",
                options: [],
              },
              {
                id: "L2",
                title: "Support email",
                q: "Which address should people write to for help?",
                options: [],
              },
            ],
          },
        ],
      },
    ],
  };
}
