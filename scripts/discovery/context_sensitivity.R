#!/usr/bin/env Rscript
arg <- grep("^--file=",commandArgs(FALSE),value=TRUE)
root <- normalizePath(file.path(dirname(gsub("~+~"," ",sub("^--file=","",arg),fixed=TRUE)),"..",".."))
suppressPackageStartupMessages({library(DESeq2);library(jsonlite)})
out <- file.path(root,"results","phase4")
counts <- as.matrix(read.csv(file.path(root,"data","processed","GSE132741","count_matrix.csv"),row.names=1,check.names=FALSE))
meta <- read.csv(file.path(out,"external_context.csv"))
stopifnot(identical(colnames(counts),meta$count_column))
rownames(meta) <- meta$count_column
meta$condition <- factor(meta$condition,levels=c("WT","mdx"))
meta$fasting_hours_centered <- (meta$fasting_minutes-mean(meta$fasting_minutes))/60
storage.mode(counts) <- "integer"
dds <- DESeqDataSetFromMatrix(counts,meta,~fasting_hours_centered+condition)
dds <- dds[rowSums(counts>=10)>=3,]
dds <- DESeq(dds,parallel=FALSE,minReplicatesForReplace=Inf)
res <- results(dds,contrast=c("condition","mdx","WT"),alpha=.05)
write.csv(data.frame(gene_id=rownames(dds),as.data.frame(res)),file.path(out,"unshrunken_fasting_adjusted.csv"),row.names=FALSE,na="")
writeLines(capture.output(sessionInfo()),file.path(out,"context_sessionInfo.txt"))
write_json(list(design="~ fasting_hours_centered + condition",reference="WT",case="mdx",genes=nrow(dds),
  DEGs=sum(!is.na(res$padj)&res$padj<.05&abs(res$log2FoldChange)>1),outlier_replacement=FALSE,
  caution="Exploratory measured-context sensitivity; fasting may be a mediator or proxy. Not proof of confounder removal. Clock times interpreted as same-day collection."),
  file.path(out,"context_sensitivity.json"),pretty=TRUE,auto_unbox=TRUE)
print(resultsNames(dds))
