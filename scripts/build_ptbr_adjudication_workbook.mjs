import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const inputPath = process.argv[2] || "data/annotations/ptbr_intent_adjudication.csv";
const metadataPath = process.argv[3] || "data/annotations/ptbr_intent_validation_queue_metadata.json";
const outputPath = process.argv[4] || "outputs/ptbr_intent_validation/ptbr_intent_adjudication.xlsx";

function parseCsv(text) {
  const rows = [];
  let row = [], value = "", quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    if (char === '"' && quoted && text[index + 1] === '"') { value += '"'; index += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === ',' && !quoted) { row.push(value); value = ""; }
    else if ((char === '\n' || char === '\r') && !quoted) {
      if (char === '\r' && text[index + 1] === '\n') index += 1;
      row.push(value); rows.push(row); row = []; value = "";
    } else value += char;
  }
  if (value || row.length) { row.push(value); rows.push(row); }
  return rows;
}

const parsed = parseCsv(await fs.readFile(inputPath, "utf8"));
const [header, ...body] = parsed;
const column = Object.fromEntries(header.map((name, index) => [name, index]));
const metadata = JSON.parse(await fs.readFile(metadataPath, "utf8"));
const disagreements = body.filter((row) => row[column.agreement] === "False");
if (!disagreements.length) throw new Error("Não há divergências para adjudicar.");

const values = disagreements.map((row) => [
  row[column.sample_id], row[column.feedback_text], row[column.intent_a], row[column.uncertain_a], row[column.notes_a],
  row[column.intent_b], row[column.uncertain_b], row[column.notes_b], "", "",
]);
const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Adjudicação");
const taxonomy = workbook.worksheets.add("Rótulos Bitext");
sheet.showGridLines = false;
taxonomy.showGridLines = false;
const headers = [["sample_id", "feedback_text", "intent_a", "uncertain_a", "notes_a", "intent_b", "uncertain_b", "notes_b", "adjudicated_intent", "adjudication_notes"]];
sheet.getRange("A1:J1").values = headers;
sheet.getRangeByIndexes(1, 0, values.length, 10).values = values;
sheet.getRange("A1:J1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center" };
sheet.getRange(`A2:J${values.length + 1}`).format = { verticalAlignment: "top" };
sheet.getRange(`B2:B${values.length + 1}`).format.wrapText = true;
sheet.getRange(`I2:J${values.length + 1}`).format.fill = "#FFF2CC";
for (const [name, width] of [["A:A", 23], ["B:B", 64], ["C:C", 25], ["D:D", 13], ["E:E", 28], ["F:F", 25], ["G:G", 13], ["H:H", 28], ["I:I", 28], ["J:J", 32]]) sheet.getRange(name).format.columnWidth = width;
sheet.freezePanes.freezeRows(1);

taxonomy.getRange("A1:B1").values = [["category", "intent"]];
taxonomy.getRange("A1:B1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
taxonomy.getRangeByIndexes(1, 0, metadata.bitext_intents.length, 2).values = metadata.bitext_intents.map((intent) => ["Original Bitext label", intent]);
taxonomy.getRange("A:A").format.columnWidth = 24;
taxonomy.getRange("B:B").format.columnWidth = 35;
sheet.getRange(`I2:I${values.length + 1}`).dataValidation = { rule: { type: "list", formula1: `'Rótulos Bitext'!$B$2:$B$${metadata.bitext_intents.length + 1}` } };

workbook.recalculate();
const check = await workbook.inspect({ kind: "table", range: "Adjudicação!A1:J6", include: "values", tableMaxRows: 6, tableMaxCols: 10 });
if (!check.ndjson.includes("adjudicated_intent")) throw new Error("Coluna de adjudicação ausente.");
const preview = await workbook.render({ sheetName: "Adjudicação", range: "A1:J8", scale: 1.3 });
await fs.mkdir(outputPath.substring(0, outputPath.lastIndexOf("/")), { recursive: true });
await fs.writeFile(outputPath.replace(/\.xlsx$/, ".png"), new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Planilha de adjudicação criada: ${outputPath}`);
