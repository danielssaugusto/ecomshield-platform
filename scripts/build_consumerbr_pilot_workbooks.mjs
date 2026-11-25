// Create two blinded human-annotation workbooks from the private pilot CSV.

import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(process.env.ECOMSHIELD_ROOT ?? path.resolve(import.meta.dirname, ".."));
const dir = path.join(root, "outputs/tp3-consumerbr");
const csvPath = path.join(dir, "pilot_development.csv");
const manifestPath = path.join(root, "reports/tp3_data/consumerbr_pilot_manifest.json");
const taxonomyPath = path.join(root, "data/processed/bitext_retail_intents_report.json");
const manifest = JSON.parse(await fs.readFile(manifestPath, "utf8"));
const taxonomyReport = JSON.parse(await fs.readFile(taxonomyPath, "utf8"));
const labels = [...Object.keys(taxonomyReport.intent_counts).sort(), "fora_de_escopo"];
if (labels.length !== 47 || manifest.development_rows !== 240) {
  throw new Error("Taxonomia ou manifesto do piloto não corresponde ao protocolo.");
}
const imported = await Workbook.fromCSV(await fs.readFile(csvPath, "utf8"), { sheetName: "Fonte" });
const source = imported.worksheets.getItemAt(0);
const headers = source.getRange("A1:D1").values[0];
if (JSON.stringify(headers) !== JSON.stringify(["sample_id", "source_id", "company", "complaint_text"])) {
  throw new Error("Colunas da fila privada mudaram.");
}
const rows = source.getRangeByIndexes(1, 0, 240, 4).values;
if (rows.length !== 240 || new Set(rows.map((r) => r[0])).size !== 240) {
  throw new Error("Fila não contém 240 IDs únicos.");
}

for (const reviewer of ["A", "B"]) {
  const book = Workbook.create();
  const sheet = book.worksheets.add("Anotação");
  const guide = book.worksheets.add("Intenções");
  sheet.showGridLines = false;
  guide.showGridLines = false;
  sheet.tabColor = "#254B70";

  sheet.getRange("A2").values = [[`Piloto ConsumerBR — anotador ${reviewer}`]];
  sheet.getRange("A2:G2").format.font = { name: "Arial", size: 14, bold: true, color: "#203348" };
  sheet.getRange("A3").values = [["Fonte: ConsumerBR, DOI 10.5281/zenodo.18022568, CC BY 4.0. Amostra de desenvolvimento: 240 relatos reais anonimizados."]];
  sheet.getRange("A4").values = [["Leia cada relato isoladamente. Não consulte o outro anotador. Preencha intenção ou incerto=sim, justificativa e seu nome. Não publique este arquivo."]];
  sheet.getRange("A3:G4").format.font = { name: "Arial", size: 10, color: "#40566B" };
  sheet.getRange("A6:G6").values = [["ID", "Texto da reclamação", "Intenção", "Incerto?", "Justificativa", "Revisor", "Situação"]];
  sheet.getRange("A6:G6").format = {
    fill: "#254B70",
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
  };
  sheet.getRange("A6:G6").format.rowHeight = 27;
  const first = 7;
  const last = first + rows.length - 1;
  sheet.getRangeByIndexes(first - 1, 0, rows.length, 2).values = rows.map((r) => [r[0], r[3]]);
  sheet.getRange(`A${first}:G${last}`).format.font = { name: "Arial", size: 10, color: "#243443" };
  sheet.getRange(`A${first}:G${last}`).format.verticalAlignment = "top";
  sheet.getRange(`B${first}:B${last}`).format.wrapText = true;
  sheet.getRange(`C${first}:F${last}`).format.fill = "#FFF1C9";
  sheet.getRange(`E${first}:E${last}`).format.wrapText = true;
  for (let i = 0; i < rows.length; i += 1) {
    const estimatedLines = Math.ceil(String(rows[i][3]).length / 105);
    sheet.getRange(`A${first + i}:G${first + i}`).format.rowHeight = Math.min(320, Math.max(44, estimatedLines * 15 + 14));
  }
  sheet.getRange(`G${first}`).formulas = [[`=IF(AND(D${first}<>"",F${first}<>"",OR(AND(C${first}<>"",D${first}="não",IF(C${first}="fora_de_escopo",E${first}<>"",TRUE)),AND(D${first}="sim",E${first}<>""))),"Completo","Pendente")`]];
  sheet.getRange(`G${first}:G${last}`).fillDown();
  sheet.getRange(`C${first}:C${last}`).dataValidation = { rule: { type: "list", formula1: "'Intenções'!$A$8:$A$54" } };
  sheet.getRange(`D${first}:D${last}`).dataValidation = { rule: { type: "list", values: ["não", "sim"] } };
  sheet.getRange("A:A").format.columnWidth = 24;
  sheet.getRange("B:B").format.columnWidth = 96;
  sheet.getRange("C:C").format.columnWidth = 32;
  sheet.getRange("D:D").format.columnWidth = 12;
  sheet.getRange("E:E").format.columnWidth = 55;
  sheet.getRange("F:F").format.columnWidth = 20;
  sheet.getRange("G:G").format.columnWidth = 16;
  sheet.freezePanes.freezeRows(6);
  sheet.freezePanes.freezeColumns(1);
  sheet.tables.add(`A6:G${last}`, true, `PilotLabels${reviewer}`);

  guide.getRange("A2").values = [["Intenções permitidas"]];
  guide.getRange("A2:C2").format.font = { name: "Arial", size: 14, bold: true, color: "#203348" };
  guide.getRange("A3").values = [["Escolha o pedido principal descrito pelo consumidor, não o produto, a empresa ou a nota."]];
  guide.getRange("A4").values = [["Use fora_de_escopo quando não houver intenção da taxonomia. Use Incerto? = sim se faltar contexto e explique."]];
  guide.getRange("A5").values = [["Fonte da taxonomia: Bitext Retail eCommerce; a classe fora_de_escopo é adicional para este piloto."]];
  guide.getRange("A7").values = [["Rótulo"]];
  guide.getRange("A7").format = { fill: "#254B70", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" } };
  guide.getRange("A8:A54").values = labels.map((label) => [label]);
  guide.getRange("A8:A54").format.font = { name: "Arial", size: 10, color: "#243443" };
  guide.getRange("A:A").format.columnWidth = 38;
  guide.getRange("B:B").format.columnWidth = 75;
  guide.freezePanes.freezeRows(7);

  sheet.getRange("C7:F7").values = [["cancel_order", "não", "Pede cancelamento", "Teste temporário"]];
  book.recalculate();
  if (sheet.getRange("G7").values[0][0] !== "Completo") {
    throw new Error("Situação não mudou após preencher os campos obrigatórios.");
  }
  sheet.getRange("C7:D7").values = [["", "sim"]];
  book.recalculate();
  if (sheet.getRange("G7").values[0][0] !== "Completo") {
    throw new Error("Incerteza justificada não foi reconhecida como preenchida.");
  }
  sheet.getRange("C7:F7").values = [["", "", "", ""]];
  book.recalculate();
  if (sheet.getRange("G7").values[0][0] !== "Pendente") {
    throw new Error("Teste temporário não foi restaurado.");
  }
  const check = await book.inspect({ kind: "table", range: "Anotação!A6:G9", include: "values,formulas", tableMaxRows: 4, tableMaxCols: 7, maxChars: 1800 });
  if (!check.ndjson.includes("Texto da reclamação") || !check.ndjson.includes("Pendente")) {
    throw new Error("Cabeçalho ou situação inicial ausente.");
  }
  const errors = await book.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, maxChars: 800 });
  if (errors.ndjson.includes("#REF!") || errors.ndjson.includes("#VALUE!")) {
    throw new Error("Erro de fórmula na fila.");
  }
  if (reviewer === "A") {
    const preview = await book.render({ sheetName: "Anotação", range: "A2:G10", scale: 1.2 });
    await fs.writeFile(path.join(dir, "preview_anotacao.png"), new Uint8Array(await preview.arrayBuffer()));
  }
  const out = path.join(dir, `piloto_anotador_${reviewer}.xlsx`);
  const xlsx = await SpreadsheetFile.exportXlsx(book);
  await xlsx.save(out);
  const reopened = await SpreadsheetFile.importXlsx(await FileBlob.load(out));
  const reread = reopened.worksheets.getItem("Anotação").getRange(`A${first}:B${last}`).values;
  if (reread.length !== 240 || reread[239][0] !== rows[239][0]) {
    throw new Error("Exportação/importação perdeu registros.");
  }
  console.log(`${out}: 240 registros; 47 opções de intenção; revisão ${reviewer}`);
}
