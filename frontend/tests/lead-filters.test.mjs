import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import vm from "node:vm";
import ts from "typescript";

// Exercise the exact production utility without adding a new test dependency.
const source = readFileSync(new URL("../src/lib/lead-filters.ts", import.meta.url), "utf8");
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText;
const context = { exports: {} };
vm.runInNewContext(compiled, context);
const { createLeadFilters, leadFilterError, leadQueryFilters } = context.exports;

test("month and year selections expand to inclusive calendar dates", () => {
  for (const [month, last] of [["2024-02", "29"], ["2026-02", "28"], ["2026-12", "31"]]) {
    const filters = leadQueryFilters({ ...createLeadFilters(), dateMode: "month", month }, true);
    assert.equal(filters.date_from, `${month}-01`);
    assert.equal(filters.date_to, `${month}-${last}`);
  }
  const year = leadQueryFilters({ ...createLeadFilters(), dateMode: "year", year: "2026" }, true);
  assert.equal(year.date_from, "2026-01-01");
  assert.equal(year.date_to, "2026-12-31");
});

test("unassigned means valid with no active owner; named Sales uses the account ID", () => {
  const unassigned = leadQueryFilters({ ...createLeadFilters("spse"), assignment: "unassigned" }, true);
  assert.equal(unassigned.status, "valid");
  assert.equal(unassigned.assignment_status, "unassigned");
  assert.equal(unassigned.source, "spse");
  const named = leadQueryFilters({ ...createLeadFilters(), assignment: "user:wok-id", salesStatus: "Closing" }, true);
  assert.equal(named.sales_user_id, "wok-id");
  assert.equal(named.sales_status, "Closing");
});

test("Sales cannot request another owner's scope through Marketing filter state", () => {
  const filters = leadQueryFilters({ ...createLeadFilters(), status: "invalid", assignment: "user:another-sales" }, false);
  assert.equal(filters.status, "all");
  assert.equal(filters.sales_user_id, undefined);
  assert.equal(filters.assignment_status, undefined);
});

test("range supports one-sided dates and ignores fields from inactive time modes", () => {
  const filters = leadQueryFilters({ ...createLeadFilters(), dateFrom: "2026-10-01", month: "2024-02", year: "2025" }, true);
  assert.equal(filters.date_from, "2026-10-01");
  assert.equal(filters.date_to, undefined);
});

test("invalid ranges and calendar values cannot be applied", () => {
  for (const change of [
    { dateFrom: "2026-11-01", dateTo: "2026-10-01" },
    { dateFrom: "2026-02-30" }, { dateTo: "1899-12-31" },
    { dateMode: "month", month: "2026-13" },
    { dateMode: "year", year: "26" }, { dateMode: "year", year: "10000" },
  ]) assert.ok(leadFilterError({ ...createLeadFilters(), ...change }));
  assert.equal(leadFilterError({ ...createLeadFilters(), dateFrom: "2024-02-29" }), null);
});
