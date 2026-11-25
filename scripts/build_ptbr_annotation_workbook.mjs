import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const queuePath = process.argv[2] || "data/annotations/ptbr_intent_validation_queue.csv";
const metadataPath = process.argv[3] || "data/annotations/ptbr_intent_validation_queue_metadata.json";
const outputPath = process.argv[4] || "outputs/ptbr_intent_validation/ptbr_intent_validation_queue.xlsx";

const csv = await fs.readFile(queuePath, "utf8");
const metadata = JSON.parse(await fs.readFile(metadataPath, "utf8"));
const rows = csv.trimEnd().split(/\r?\n/).slice(1).map((line) => {
  const values = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"' && line[i + 1] === '"' && quoted) { value += '"'; i += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === ',' && !quoted) { values.push(value); value = ""; }
    else value += char;
  }
  values.push(value);
  return values;
});

const workbook = Workbook.create();
const queue = workbook.worksheets.add("Fila de anotação");
const taxonomy = workbook.worksheets.add("Rótulos Bitext");
queue.showGridLines = false;
taxonomy.showGridLines = false;
queue.getRange("A1:E1").values = [["sample_id", "feedback_text", "intent", "uncertain", "notes"]];
queue.getRangeByIndexes(1, 0, rows.length, 5).values = rows;
queue.getRange("A1:E1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center" };
queue.getRange(`A2:E${rows.length + 1}`).format = { verticalAlignment: "top" };
queue.getRange(`B2:B${rows.length + 1}`).format.wrapText = true;
queue.getRange(`C2:E${rows.length + 1}`).format.fill = "#FFF2CC";
queue.getRange("A:A").format.columnWidth = 23;
queue.getRange("B:B").format.columnWidth = 70;
queue.getRange("C:C").format.columnWidth = 30;
queue.getRange("D:D").format.columnWidth = 12;
queue.getRange("E:E").format.columnWidth = 35;
queue.freezePanes.freezeRows(1);
queue.getRange(`C2:C${rows.length + 1}`).dataValidation = { rule: { type: "list", formula1: `'Rótulos Bitext'!$B$2:$B$${metadata.bitext_intents.length + 1}` } };
queue.getRange(`D2:D${rows.length + 1}`).dataValidation = { rule: { type: "list", values: ["yes", "no"] } };

taxonomy.getRange("A1:B1").values = [["category", "intent"]];
taxonomy.getRange("A1:B1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
taxonomy.getRangeByIndexes(1, 0, metadata.bitext_intents.length, 2).values = metadata.bitext_intents.map((intent) => ["Original Bitext label", intent]);
taxonomy.getRange("A:A").format.columnWidth = 24;
taxonomy.getRange("B:B").format.columnWidth = 35;
taxonomy.freezePanes.freezeRows(1);

workbook.recalculate();
const check = await workbook.inspect({ kind: "table", range: "Fila de anotação!A1:E6", include: "values", tableMaxRows: 6, tableMaxCols: 5 });
if (!check.ndjson.includes("feedback_text")) throw new Error("Fila não foi preenchida corretamente.");
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 20 } });
if (errors.ndjson.includes("#REF!") || errors.ndjson.includes("#VALUE!")) throw new Error("Erro de fórmula no workbook.");
const preview = await workbook.render({ sheetName: "Fila de anotação", range: "A1:E12", scale: 1.5 });
await fs.mkdir(outputPath.substring(0, outputPath.lastIndexOf("/")), { recursive: true });
await fs.writeFile(outputPath.replace(/\.xlsx$/, ".png"), new Uint8Array(await preview.arrayBuffer()));
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`Workbook criado: ${outputPath}`);
