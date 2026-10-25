/** Build the private ConsumerBR adjudication workbook from human-review evidence. */
import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.env.ECOMSHIELD_ROOT || process.cwd();
const privateDir = `${root}/outputs/tp3-consumerbr`;
const records = JSON.parse(await fs.readFile(`${privateDir}/adjudication_input.json`, "utf8"));
const taxonomy = JSON.parse(await fs.readFile(`${root}/data/processed/bitext_retail_intents_report.json`, "utf8"));
const labels = [...Object.keys(taxonomy.intent_counts).sort(), "fora_de_escopo"];
if (records.length !== 167 || labels.length !== 47) throw new Error("Entrada ou taxonomia inesperada.");

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Adjudicação");
const options = workbook.worksheets.add("Opções");
sheet.showGridLines = false;
sheet.getRange("A2").values = [["Adjudicação ConsumerBR — casos com divergência ou incerteza"]];
sheet.getRange("A3").values = [["Decida a intenção principal sem consultar modelos, nota ou empresa. Justifique toda decisão final; use fora_de_escopo somente quando nenhuma intenção contemplar o pedido."]];
sheet.getRange("A4").values = [["Registre seu nome em Adjudicador. Não altere IDs, texto ou avaliações originais. Esta planilha contém relatos reais anonimizados e deve permanecer privada."]];
sheet.mergeCells("A3:L3");
sheet.mergeCells("A4:L4");
sheet.getRange("A2").format = { font: { name: "Arial", size: 14, bold: true, color: "#203348" } };
sheet.getRange("A3:A4").format = { font: { name: "Arial", size: 10, color: "#40566B" }, wrapText: true };
sheet.getRange("A3:A4").format.rowHeight = 28;

const headers = [["ID", "Texto da reclamação", "Intenção Luana", "Incerto? Luana", "Justificativa Luana", "Intenção Daniel", "Incerto? Daniel", "Justificativa Daniel", "Decisão final", "Justificativa da adjudicação", "Adjudicador", "Situação"]];
sheet.getRange("A6:L6").values = headers;
sheet.getRange("A6:L6").format = { fill: "#254B70", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center", verticalAlignment: "center", wrapText: true };
sheet.getRange("A6:L6").format.rowHeight = 30;
const first = 7;
const last = first + records.length - 1;
sheet.getRange(`A${first}:K${last}`).values = records.map((row) => [
  row.sample_id, row.complaint_text, row.intent_a, row.uncertain_a, row.notes_a,
  row.intent_b, row.uncertain_b, row.notes_b, "", "", "",
]);
for (let row = first; row <= last; row += 1) {
  sheet.getRange(`L${row}`).formulas = [[`=IF(AND(I${row}<>"",J${row}<>"",K${row}<>""),"Completo","Pendente")`]];
}
sheet.getRange(`A${first}:L${last}`).format.font = { name: "Arial", size: 10, color: "#203348" };
sheet.getRange(`A${first}:L${last}`).format.verticalAlignment = "top";
sheet.getRange(`B${first}:B${last}`).format.wrapText = true;
sheet.getRange(`E${first}:J${last}`).format.wrapText = true;
sheet.getRange(`A${first}:L${last}`).format.borders = { preset: "all", style: "thin", color: "#D5DEE8" };
sheet.getRange(`I${first}:K${last}`).format.fill = "#FFF2CC";
sheet.getRange(`A${first}:H${last}`).format.fill = "#EAF2F8";
sheet.getRange(`L${first}:L${last}`).format.fill = "#EAF2F8";
for (let i = 0; i < records.length; i += 1) {
  const lineEstimate = Math.ceil(String(records[i].complaint_text).length / 110);
  sheet.getRange(`A${first + i}:L${first + i}`).format.rowHeight = Math.min(300, Math.max(48, lineEstimate * 14 + 16));
}
sheet.getRange(`I${first}:I${last}`).dataValidation = { rule: { type: "list", formula1: "'Opções'!$A$2:$A$48" } };
sheet.freezePanes.freezeRows(6);
sheet.freezePanes.freezeColumns(2);
sheet.getRange("A:A").format.columnWidth = 22;
sheet.getRange("B:B").format.columnWidth = 78;
sheet.getRange("C:C").format.columnWidth = 21;
sheet.getRange("D:D").format.columnWidth = 14;
sheet.getRange("E:E").format.columnWidth = 32;
sheet.getRange("F:F").format.columnWidth = 21;
sheet.getRange("G:G").format.columnWidth = 14;
sheet.getRange("H:H").format.columnWidth = 32;
sheet.getRange("I:I").format.columnWidth = 22;
sheet.getRange("J:J").format.columnWidth = 36;
sheet.getRange("K:K").format.columnWidth = 24;
sheet.getRange("L:L").format.columnWidth = 14;
sheet.tables.add(`A6:L${last}`, true, "ConsumerBRAdjudication").style = "TableStyleMedium2";

options.getRange("A1:B1").values = [["Intenção", "Uso"]];
options.getRange("A1:B1").format = { fill: "#254B70", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" } };
options.getRange("A2:B48").values = labels.map((label) => [label, label === "fora_de_escopo" ? "Taxonomia não contempla o pedido principal" : "Rótulo Bitext original"]);
options.getRange("A1:B48").format.font = { name: "Arial", size: 10, color: "#203348" };
options.getRange("A:A").format.columnWidth = 28;
options.getRange("B:B").format.columnWidth = 48;
options.freezePanes.freezeRows(1);
options.tables.add("A1:B48", true, "IntentOptions").style = "TableStyleMedium2";

workbook.recalculate();
const check = await workbook.inspect({ kind: "table", range: "Adjudicação!A6:L9", include: "values,formulas", tableMaxRows: 4, tableMaxCols: 12, maxChars: 2600 });
if (!check.ndjson.includes("Decisão final") || !check.ndjson.includes("Pendente")) throw new Error("Estrutura de adjudicação inválida.");
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, maxChars: 800 });
if (errors.ndjson.includes("#REF!") || errors.ndjson.includes("#VALUE!")) throw new Error("Erro de fórmula na planilha de adjudicação.");
const preview = await workbook.render({ sheetName: "Adjudicação", range: "A1:L10", scale: 1.25, format: "png" });
await fs.writeFile(`${privateDir}/preview_adjudication.png`, new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(`${privateDir}/consumerbr_adjudication_queue.xlsx`);
console.log(`Planilha criada com ${records.length} casos para adjudicação.`);
