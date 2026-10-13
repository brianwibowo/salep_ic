export interface ParsedSpseContent {
  title: string;
  badge: {
    text: string;
    variant: "warning" | "destructive" | "info" | "neutral";
  } | null;
  stage: string;
  agency: string;
  hps: string;
  rawRemainder?: string;
}

/**
 * Parses raw SPSE lead content string from scraper/database.
 * Extracts:
 * - Clean package title (with embedded HTML removed)
 * - Status badge (e.g. "Tender Gagal", "Tender Ulang", "Seleksi Ulang")
 * - Current tender stage (Tahap tender saat ini)
 * - Agency / Instansi
 * - HPS amount (Nilai HPS)
 */
export function parseSpseLeadContent(
  content: string | undefined | null,
  fallbackAgency?: string | null,
): ParsedSpseContent {
  const text = (content || "").trim();

  // 1. Extract status badge if present (e.g. from <span class='badge badge-warning'>Tender Gagal</span>)
  let badge: ParsedSpseContent["badge"] = null;
  const badgeMatch =
    text.match(/<span[^>]*class=['"][^'"]*badge[^'"]*['"][^>]*>([\s\S]*?)<\/span>/i) ||
    text.match(/<span[^>]*>([\s\S]*?)<\/span>/i);

  if (badgeMatch) {
    const rawBadgeText = badgeMatch[1].replace(/<[^>]+>/g, "").trim();
    if (rawBadgeText) {
      const lower = rawBadgeText.toLowerCase();
      let variant: "warning" | "destructive" | "info" | "neutral" = "info";

      if (lower.includes("gagal") || lower.includes("batal")) {
        variant = "destructive";
      } else if (lower.includes("ulang")) {
        variant = "warning";
      } else if (lower.includes("selesai")) {
        variant = "neutral";
      }

      badge = {
        text: rawBadgeText,
        variant,
      };
    }
  }

  // 2. Extract title section
  const titleMatch = text.match(
    /Nama paket:\s*([\s\S]*?)(?=\n|Tahap tender saat ini:|Instansi:|Nilai HPS:|$)/i,
  );
  let rawTitle = titleMatch ? titleMatch[1] : text.split("\n")[0] || "";

  // Remove the badge span completely from rawTitle so the title does not duplicate the badge text
  rawTitle = rawTitle.replace(/<span[^>]*>[\s\S]*?<\/span>/gi, " ");
  // Strip any remaining HTML tags and collapse whitespace
  const cleanTitle = rawTitle
    .replace(/<[^>]+>/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  // 3. Extract stage
  const stageMatch = text.match(
    /Tahap tender saat ini:\s*([\s\S]*?)(?=\n|Instansi:|Nilai HPS:|Detail:|$)/i,
  );
  const cleanStage = stageMatch
    ? stageMatch[1].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()
    : "";

  // 4. Extract HPS
  const hpsMatch = text.match(/Nilai HPS:\s*([\s\S]*?)(?=\n|Detail:|$)/i);
  const cleanHps = hpsMatch
    ? hpsMatch[1].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()
    : "";

  // 5. Extract agency/instansi
  const agencyMatch = text.match(
    /Instansi:\s*([\s\S]*?)(?=\n|Nilai HPS:|Detail:|$)/i,
  );
  const cleanAgency = agencyMatch
    ? agencyMatch[1].replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim()
    : fallbackAgency?.trim() || "";

  return {
    title: cleanTitle || fallbackAgency || "Paket Pengadaan SPSE",
    badge,
    stage: cleanStage,
    agency: cleanAgency,
    hps: cleanHps,
  };
}
