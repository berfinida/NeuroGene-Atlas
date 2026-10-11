#!/usr/bin/env Rscript
arg <- grep("^--file=",commandArgs(FALSE),value=TRUE)
root <- normalizePath(file.path(dirname(gsub("~+~"," ",sub("^--file=","",arg),fixed=TRUE)),"..",".."))
suppressPackageStartupMessages({library(DESeq2);library(jsonlite)})
out <- file.path(root,"results","phase4","qc")
dir.create(out,recursive=TRUE,showWarnings=FALSE)
audit <- list()
for (study in c("GSE156496","GSE132741","GSE284723")) {
  dds <- readRDS(file.path(root,"results",study,"deseq2","dds.rds"))
  levels <- levels(dds$condition)
  res <- results(dds,contrast=c("condition",levels[2],levels[1]),alpha=.05)
  reverse <- results(dds,contrast=c("condition",levels[1],levels[2]),alpha=.05)
  stopifnot(isTRUE(all.equal(res$log2FoldChange,-reverse$log2FoldChange)))
  name <- if (study=="GSE156496") "deseq2_D51_vs_WT_unshrunken.csv" else "unshrunken.csv"
  saved <- read.csv(file.path(root,"results",study,"deseq2",name))
  stopifnot(identical(rownames(dds),saved$gene_id))
  difference <- max(abs(res$log2FoldChange-saved$log2FoldChange),na.rm=TRUE)
  stopifnot(difference<1e-8)
  valid <- !is.na(res$padj)
  stopifnot(max(abs(p.adjust(res$pvalue[valid],"BH")-res$padj[valid]),na.rm=TRUE)<1e-8)
  vsd <- vst(dds,blind=FALSE)
  pca <- plotPCA(vsd,intgroup="condition",returnData=TRUE)
  pca$PC1_percent_variance <- attr(pca,"percentVar")[1]*100
  pca$PC2_percent_variance <- attr(pca,"percentVar")[2]*100
  write.csv(pca,file.path(out,paste0(study,"_pca.csv")),row.names=FALSE)
  write.csv(as.matrix(dist(t(assay(vsd)))),file.path(out,paste0(study,"_distances.csv")))
  cooks <- assays(dds)[["cooks"]]
  samples <- data.frame(sample=colnames(dds),condition=dds$condition,
    library_size=colSums(counts(dds)),size_factor=sizeFactors(dds),
    median_cooks=apply(cooks,2,median,na.rm=TRUE),max_cooks=apply(cooks,2,max,na.rm=TRUE))
  write.csv(samples,file.path(out,paste0(study,"_samples.csv")),row.names=FALSE)
  audit[[study]] <- list(design=paste(deparse(design(dds)),collapse=""),reference=levels[1],case=levels[2],
    samples=ncol(dds),genes=nrow(dds),pvalue_missing=sum(is.na(res$pvalue)),padj_missing=sum(is.na(res$padj)),
    reversal_verified=TRUE,BH_verified=TRUE,stored_fit_max_abs_difference=difference,
    raw_counts_integer=all(counts(dds)==floor(counts(dds))),
    independent_filter_threshold=unname(metadata(res)$filterThreshold),
    max_cooks_cutoff=qf(.99,ncol(model.matrix(design(dds),as.data.frame(colData(dds)))),ncol(dds)-ncol(model.matrix(design(dds),as.data.frame(colData(dds))))),
    versions=list(R=R.version.string,DESeq2=as.character(packageVersion("DESeq2"))))
}
write_json(audit,file.path(out,"fit_audit.json"),pretty=TRUE,auto_unbox=TRUE)
print(audit)
