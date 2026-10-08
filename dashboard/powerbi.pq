// Power Query: create a blank query named Entries and paste this code.
// Credentials are entered in the Power BI connection dialog, never in this file.
let
    Source = PostgreSQL.Database("localhost:5434", "music"),
    Entries = Source{[Schema="dw", Item="v_entries"]}[Data]
in
    Entries
