#!/usr/bin/env Rscript
file_arg <- grep("^--file=", commandArgs(FALSE), value=TRUE)
stopifnot(length(file_arg)==1)
root <- normalizePath(file.path(dirname(gsub("~+~", " ", sub("^--file=", "", file_arg), fixed=TRUE)), "..", ".."))
suppressPackageStartupMessages({library(DESeq2); library(apeglm); library(jsonlite)})
set.seed(284723)
input <- file.path(root,"data","processed","GSE284723")
out <- file.path(root,"results","GSE284723","deseq2")
dir.create(out,recursive=TRUE,showWarnings=FALSE)
count_data <- as.matrix(read.csv(file.path(input,"count_matrix.csv"),row.names=1,check.names=FALSE))
meta <- read.csv(file.path(input,"sample_metadata.csv"),stringsAsFactors=FALSE)
stopifnot(identical(colnames(count_data),meta$count_column),!anyDuplicated(rownames(count_data)),
          !anyDuplicated(meta$accession),all(count_data>=0),all(is.finite(count_data)),
          all(count_data==floor(count_data)),sum(meta$condition=="Control")==5,sum(meta$condition=="mKO")==4)
rownames(meta) <- meta$count_column
meta$condition <- factor(meta$condition,levels=c("Control","mKO"))
storage.mode(count_data) <- "integer"
export <- function(x,name) write.csv(data.frame(gene_id=rownames(x),as.data.frame(x)),file.path(out,name),row.names=FALSE,na="")
summaries <- list()
for (scenario in c("default","count20","minimum4")) {
  threshold <- if (scenario=="count20") 20 else 10
  minimum <- if (scenario=="minimum4") 4 else 3
  dds <- DESeqDataSetFromMatrix(count_data,meta,~condition)
  dds <- dds[rowSums(count_data>=threshold)>=minimum,]
  dds <- DESeq(dds,parallel=FALSE)
  res <- results(dds,contrast=c("condition","mKO","Control"),alpha=.05,pAdjustMethod="BH")
  reverse <- results(dds,contrast=c("condition","Control","mKO"),alpha=.05)
  stopifnot(isTRUE(all.equal(res$log2FoldChange,-reverse$log2FoldChange)))
  export(res,if(scenario=="default") "unshrunken.csv" else paste0("unshrunken_",scenario,".csv"))
  sig <- !is.na(res$padj)&res$padj<.05&abs(res$log2FoldChange)>1
  summaries[[scenario]] <- list(genes_tested=nrow(dds),valid_padj=sum(!is.na(res$padj)),degs=sum(sig),
    up=sum(sig&res$log2FoldChange>0),down=sum(sig&res$log2FoldChange<0),minimum_count=threshold,
    minimum_samples=minimum,filter_threshold=unname(metadata(res)$filterThreshold))
  if (scenario=="default") {
    export(lfcShrink(dds,coef="condition_mKO_vs_Control",res=res,type="apeglm"),"apeglm.csv")
    export(results(dds,contrast=c("condition","mKO","Control"),alpha=.05,cooksCutoff=FALSE),"unshrunken_no_cooks.csv")
    saveRDS(dds,file.path(out,"dds.rds"))
    write.csv(counts(dds,normalized=TRUE),file.path(out,"normalized_counts.csv"))
    vsd <- vst(dds,blind=FALSE)
    write.csv(assay(vsd),file.path(out,"vst_counts.csv"))
    pca <- plotPCA(vsd,intgroup="condition",returnData=TRUE)
    write.csv(pca,file.path(out,"pca_samples.csv"),row.names=FALSE)
    write_json(as.list(attr(pca,"percentVar")),file.path(out,"pca_percent_variance.json"),auto_unbox=TRUE)
    write.csv(as.matrix(dist(t(assay(vsd)))),file.path(out,"sample_distances.csv"))
    write.csv(meta,file.path(out,"sample_metadata.csv"),row.names=FALSE)
  }
}
writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
summary <- list(status="complete",accession="GSE284723",contrast="mKO_vs_Control",design="~ condition",reference="Control",
  groups=as.list(table(meta$condition)),alpha=.05,p_adjust="BH",independent_filtering=TRUE,
  outlier_replacement="Not eligible: neither group has seven replicates",scenarios=summaries,
  versions=list(R=R.version.string,DESeq2=as.character(packageVersion("DESeq2")),apeglm=as.character(packageVersion("apeglm")),jsonlite=as.character(packageVersion("jsonlite"))))
write_json(summary,file.path(out,"summary.json"),pretty=TRUE,auto_unbox=TRUE)
print(summary)
