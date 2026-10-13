// Review data for the export feature (lets-align review page).
window.REVIEW = {
  id: "notes-export",
  project: "Notes app",
  title: "export review",
  source: "PLAN.md (open decisions 1–4)",
  page: ".review/notes-export/index.html",
  context:
    "A small notes app. Users asked to download their notes. These are the choices the export work needs before the build starts.",
  rounds: [
    {
      id: "now",
      title: "Round 1: before we build export",
      needed_by: "the export build",
      status: "open",
      groups: [
        {
          id: "file",
          title: "The downloaded file",
          items: [
            {
              id: "D1",
              title: "File format",
              rec: 0,
              q: "In which format should the notes download?",
              options: [
                { label: "Markdown", pro: "Opens well in most note apps.", con: "Shows small marks like # in a plain editor." },
                { label: "Plain text", pro: "Opens anywhere.", con: "Headings and lists lose their shape." },
              ],
            },
            {
              id: "D2",
              title: "One file or many",
              rec: 0,
              q: "Should the download be one file, or one file per note?",
              options: [
                { label: "One file with all notes", pro: "One click, one file.", con: "A long file is hard to split later." },
                { label: "One file per note, in a zip", pro: "Each note stays separate.", con: "People must unzip it first." },
              ],
            },
            {
              id: "D3",
              title: "Deleted notes",
              rec: 1,
              q: "Should the download include notes that the user deleted?",
              options: [
                { label: "Yes", pro: "Nothing is lost.", con: "People may see notes they wanted gone." },
                { label: "No", pro: "The download matches what people see.", con: "A deleted note cannot come back this way." },
              ],
            },
            {
              id: "D4",
              title: "Button place",
              rec: 0,
              q: "Where should the download button be?",
              options: [
                { label: "At the top of the notes list", pro: "Easy to find.", con: "Takes space on small screens." },
                { label: "In the settings page", pro: "Keeps the list clean.", con: "Harder to find." },
              ],
            },
          ],
        },
      ],
    },
    {
      id: "later",
      title: "Round 2: before the first release",
      needed_by: "the first release",
      status: "closed",
      groups: [
        {
          id: "release",
          title: "Release",
          items: [{ id: "L1", title: "Release note", q: "Should the release note mention export?", options: [] }],
        },
      ],
    },
  ],
};
