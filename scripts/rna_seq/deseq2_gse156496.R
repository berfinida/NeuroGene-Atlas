#!/usr/bin/env Rscript
script_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
if (length(script_arg) != 1L) stop("Run with Rscript.")
# Rscript encodes spaces as ~+~ in --file on some builds.
script_path <- normalizePath(gsub("~+~", " ", sub("^--file=", "", script_arg), fixed = TRUE), mustWork = TRUE)
root <- normalizePath(file.path(dirname(script_path), "..", ".."), mustWork = TRUE)
suppressPackageStartupMessages({library(DESeq2); library(apeglm); library(jsonlite)})
set.seed(156496)
cfg <- fromJSON(file.path(root, "config", "gse156496.json"))
out <- Sys.getenv("NEUROGENE_OUTPUT_DIR", file.path(root, "results", cfg$accession, "deseq2"))
dir.create(out, recursive = TRUE, showWarnings = FALSE)
fig <- file.path(out, "figures")
dir.create(fig, showWarnings = FALSE)
input_dir <- Sys.getenv("NEUROGENE_INPUT_DIR", file.path(root, "data", "processed", cfg$accession))
counts_path <- file.path(input_dir, "count_matrix.csv")
metadata_path <- file.path(input_dir, "sample_metadata.csv")
count_data <- as.matrix(read.csv(counts_path, row.names = 1, check.names = FALSE))
meta <- read.csv(metadata_path, stringsAsFactors = FALSE)
stopifnot(!anyDuplicated(rownames(count_data)), all(grepl("^ENSMUSG[0-9]+$", rownames(count_data))),
          !anyDuplicated(meta$count_column), !anyDuplicated(meta$geo_accession),
          setequal(colnames(count_data), meta$count_column), nrow(meta) == 6L,
          all(is.finite(count_data)), all(count_data >= 0),
          all(count_data == floor(count_data)), max(count_data) <= .Machine$integer.max)
expected <- cfg$expected_samples
idx <- match(expected$count_column, meta$count_column)
stopifnot(!anyNA(idx))
meta <- meta[idx, ]
stopifnot(identical(meta$geo_accession, expected$geo_accession),
          identical(meta$condition, expected$condition),
          identical(meta$validated_condition, meta$condition), all(meta$organism == cfg$organism))
rownames(meta) <- meta$count_column
count_data <- count_data[, meta$count_column, drop = FALSE]
stopifnot(identical(colnames(count_data), rownames(meta)))
storage.mode(count_data) <- "integer"
meta$condition <- factor(meta$condition, levels = c(cfg$reference_group, cfg$case_group))
dds <- DESeqDataSetFromMatrix(count_data, meta, design = ~ condition)
keep <- rowSums(count_data >= cfg$low_count_filter$minimum_count) >= cfg$low_count_filter$minimum_samples
dds <- dds[keep, ]
dds <- DESeq(dds, parallel = FALSE)
alpha <- cfg$deg_thresholds$adjusted_p_value
lfc_cutoff <- cfg$deg_thresholds$absolute_log2_fold_change
res <- results(dds, contrast = c("condition", cfg$case_group, cfg$reference_group),
               alpha = alpha, pAdjustMethod = "BH", independentFiltering = TRUE)
coef_name <- paste0("condition_", cfg$case_group, "_vs_", cfg$reference_group)
stopifnot(coef_name %in% resultsNames(dds))
coef_res <- results(dds, name = coef_name, alpha = alpha)
stopifnot(isTRUE(all.equal(res$log2FoldChange, coef_res$log2FoldChange)))
reverse <- results(dds, contrast = c("condition", cfg$reference_group, cfg$case_group), alpha = alpha)
stopifnot(isTRUE(all.equal(res$log2FoldChange, -reverse$log2FoldChange)),
          isTRUE(all.equal(res$pvalue, reverse$pvalue)))
shrunk <- lfcShrink(dds, coef = coef_name, res = res, type = "apeglm", parallel = FALSE)
raw_path <- file.path(root, "data", "raw", cfg$accession, "GSE156496_RNAseq_RawCountTable.txt.gz")
raw <- read.delim(gzfile(raw_path), check.names = FALSE)
stopifnot(identical(rownames(count_data), raw$Geneid),
          all(count_data == as.matrix(raw[, meta$count_column])))
symbols <- raw$GeneName[match(rownames(dds), raw$Geneid)]
export <- function(result, name) {
  tab <- data.frame(gene_id = rownames(result), gene_symbol = symbols, as.data.frame(result), check.names = FALSE)
  write.csv(tab, file.path(out, name), row.names = FALSE, na = "")
  tab
}
unshrunken <- export(res, "deseq2_D51_vs_WT_unshrunken.csv")
shrunken <- export(shrunk, "deseq2_D51_vs_WT_apeglm.csv")
write.csv(counts(dds, normalized = TRUE), file.path(out, "normalized_counts.csv"))
write.csv(data.frame(meta, size_factor = sizeFactors(dds), library_size = colSums(count_data)),
          file.path(out, "sample_metadata.csv"), row.names = FALSE)
vsd <- vst(dds, blind = FALSE)
write.csv(assay(vsd), file.path(out, "vst_counts.csv"))
pca <- plotPCA(vsd, intgroup = "condition", returnData = TRUE)
pca$PC1_percent_variance <- 100 * attr(pca, "percentVar")[1]
pca$PC2_percent_variance <- 100 * attr(pca, "percentVar")[2]
write.csv(pca, file.path(out, "pca_samples.csv"), row.names = FALSE)
distances <- as.matrix(dist(t(assay(vsd))))
write.csv(distances, file.path(out, "sample_distances.csv"))
significant <- !is.na(res$padj) & res$padj < alpha & abs(res$log2FoldChange) > lfc_cutoff
color <- ifelse(significant, ifelse(res$log2FoldChange > 0, "#b83957", "#148780"), "#bbc2c4")
draw <- function(name, fn, width = 9, height = 7) {
  for (extension in c("png", "pdf")) {
    path <- file.path(fig, paste0(name, ".", extension))
    if (extension == "png") png(path, width = width, height = height, units = "in", res = 160, type = "cairo")
    else pdf(path, width = width, height = height)
    fn()
    dev.off()
  }
}
draw("pca", function() {
  cols <- ifelse(pca$condition == "WT", "#148780", "#b83957")
  plot(pca$PC1, pca$PC2, col = cols, pch = 19, cex = 1.5,
       xlab = sprintf("PC1 (%.1f%%)", pca$PC1_percent_variance[1]),
       ylab = sprintf("PC2 (%.1f%%)", pca$PC2_percent_variance[1]), main = "GSE156496: DESeq2 VST PCA")
  text(pca$PC1, pca$PC2, labels = pca$name, pos = 3, cex = 0.8)
  legend("bottomleft", c("WT", "D51"), col = c("#148780", "#b83957"), pch = 19)
})
draw("volcano", function() {
  plot(res$log2FoldChange, -log10(pmax(res$padj, 1e-300)), col = color, pch = 16, cex = 0.5,
       xlab = "Unshrunken log2 fold change (D51 / WT)", ylab = "-log10 BH adjusted p-value", main = "DESeq2 volcano")
  abline(v = c(-lfc_cutoff, lfc_cutoff), h = -log10(alpha), lty = 2)
})
draw("ma", function() {
  plot(res$baseMean, shrunk$log2FoldChange, log = "x", col = color, pch = 16, cex = 0.5,
       xlab = "Mean normalized count", ylab = "apeglm log2 fold change (D51 / WT)", main = "DESeq2 MA")
  abline(h = 0, lty = 2)
})
top <- head(order(res$padj, na.last = NA), 30)
heat <- t(scale(t(assay(vsd)[top, , drop = FALSE])))
rownames(heat) <- make.unique(paste(symbols[top], rownames(dds)[top]))
write.csv(heat, file.path(out, "heatmap_row_zscores.csv"))
draw("heatmap", function() {
  heatmap(heat, Colv = NA, scale = "none", margins = c(8, 17),
          col = colorRampPalette(c("#148780", "#ffffff", "#b83957"))(101),
          main = "Top 30 genes by BH padj: VST row z-score")
}, height = 10)
draw("sample_distance", function() {
  heatmap(distances, symm = TRUE, scale = "none", margins = c(8, 8),
          col = colorRampPalette(c("#ffffff", "#148780"))(101), main = "Euclidean distance: DESeq2 VST")
})
bh_idx <- which(!is.na(res$padj))
stopifnot(isTRUE(all.equal(res$padj[bh_idx], p.adjust(res$pvalue[bh_idx], method = "BH"), tolerance = 1e-10)),
          identical(res$padj, shrunk$padj), identical(res$pvalue, shrunk$pvalue))
saveRDS(dds, file.path(out, "dds.rds"))
writeLines(capture.output(sessionInfo()), file.path(out, "sessionInfo.txt"))
summary <- list(status = "complete", method = "DESeq2 Wald test", accession = cfg$accession,
  completed_at_utc = format(Sys.time(), tz = "UTC", usetz = TRUE), contrast = cfg$contrast,
  positive_log2fc = "Higher expression in D51 than WT", reference_group = cfg$reference_group,
  design = "~ condition", alpha = alpha, absolute_lfc_cutoff = lfc_cutoff,
  deg_lfc_source = "unshrunken", p_adjust_method = "BH", independent_filtering = TRUE,
  independent_filter_threshold = unname(metadata(res)$filterThreshold), cooks_cutoff = "DESeq2 default",
  low_count_filter = cfg$low_count_filter, raw_genes = nrow(count_data), genes_tested = nrow(dds),
  genes_with_pvalue = sum(!is.na(res$pvalue)), genes_with_padj = sum(!is.na(res$padj)),
  significant_padj = sum(res$padj < alpha, na.rm = TRUE),
  significant_padj_0_05_abs_lfc_1 = sum(significant),
  upregulated = sum(significant & res$log2FoldChange > 0), downregulated = sum(significant & res$log2FoldChange < 0),
  transformation = "VST blind=FALSE", pca_ntop = 500, heatmap_top_n = length(top), seed = 156496,
  validation = list(integer_counts = TRUE, raw_counts_match = TRUE, sample_alignment = TRUE,
                    contrast_reversal = TRUE, bh_adjustment = TRUE, ensembl_identifiers = TRUE),
  sources = cfg$sources, package_versions = list(R = R.version.string,
    DESeq2 = as.character(packageVersion("DESeq2")), apeglm = as.character(packageVersion("apeglm")),
    jsonlite = as.character(packageVersion("jsonlite"))))
write_json(summary, file.path(out, "summary.json"), pretty = TRUE, auto_unbox = TRUE, na = "null")
print(summary[c("genes_tested", "significant_padj", "significant_padj_0_05_abs_lfc_1", "upregulated", "downregulated")])
