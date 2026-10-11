#!/usr/bin/env Rscript
file_arg <- grep("^--file=", commandArgs(FALSE), value = TRUE)
root <- normalizePath(file.path(dirname(gsub("~+~", " ", sub("^--file=", "", file_arg), fixed = TRUE)), "..", ".."))
suppressPackageStartupMessages({library(DESeq2); library(apeglm); library(jsonlite)})
set.seed(132741)
input <- file.path(root,"data","processed","GSE132741")
out <- file.path(root,"results","GSE132741","deseq2")
dir.create(out,recursive=TRUE,showWarnings=FALSE)
count_data <- as.matrix(read.csv(file.path(input,"count_matrix.csv"),row.names=1,check.names=FALSE))
meta <- read.csv(file.path(input,"sample_metadata.csv"),stringsAsFactors=FALSE)
stopifnot(all(is.finite(count_data)),all(count_data>=0),all(count_data==floor(count_data)),
          !anyDuplicated(rownames(count_data)),!anyDuplicated(meta$mouse_id), all(meta$organism=="Mus musculus"),
          identical(colnames(count_data),meta$count_column),all(meta$age_weeks==30), all(meta$genotype==meta$condition))
rownames(meta) <- meta$count_column
meta$condition <- factor(meta$condition,levels=c("WT","mdx"))
storage.mode(count_data) <- "integer"
dds <- DESeqDataSetFromMatrix(count_data,meta,~condition)
dds <- dds[rowSums(count_data>=10)>=3,]
dds <- DESeq(dds,parallel=FALSE)
res <- results(dds,contrast=c("condition","mdx","WT"),alpha=.05,pAdjustMethod="BH")
reverse <- results(dds,contrast=c("condition","WT","mdx"),alpha=.05)
stopifnot(isTRUE(all.equal(res$log2FoldChange,-reverse$log2FoldChange)))
shrunk <- lfcShrink(dds,coef="condition_mdx_vs_WT",res=res,type="apeglm")
bridge <- read.csv(file.path(input,"symbol_bridge.csv"),stringsAsFactors=FALSE)
symbol <- bridge$GeneName[match(rownames(dds),bridge$gene_id)]
export <- function(x,name) write.csv(data.frame(gene_id=rownames(x),gene_symbol=symbol,as.data.frame(x)),file.path(out,name),row.names=FALSE,na="")
export(res,"unshrunken.csv")
export(shrunk,"apeglm.csv")
saveRDS(dds,file.path(out,"dds.rds"))
replaced <- if ("replace" %in% names(mcols(dds))) sum(mcols(dds)$replace,na.rm=TRUE) else 0L
write.csv(data.frame(gene_id=rownames(dds),outlier_replaced=if ("replace" %in% names(mcols(dds))) mcols(dds)$replace else FALSE),
          file.path(out,"outlier_replacement.csv"),row.names=FALSE)
dds_no_replace <- DESeqDataSetFromMatrix(count_data,meta,~condition)
dds_no_replace <- dds_no_replace[rowSums(count_data>=10)>=3,]
dds_no_replace <- DESeq(dds_no_replace,parallel=FALSE,minReplicatesForReplace=Inf)
no_replace <- results(dds_no_replace,contrast=c("condition","mdx","WT"),alpha=.05,pAdjustMethod="BH")
export(no_replace,"unshrunken_no_replacement.csv")
write.csv(counts(dds,normalized=TRUE),file.path(out,"normalized_counts.csv"))
vsd <- vst(dds,blind=FALSE)
write.csv(plotPCA(vsd,intgroup="condition",returnData=TRUE),file.path(out,"pca_samples.csv"),row.names=FALSE)
writeLines(capture.output(sessionInfo()),file.path(out,"sessionInfo.txt"))
significant <- !is.na(res$padj)&res$padj<.05&abs(res$log2FoldChange)>1
summary <- list(status="complete",accession="GSE132741",contrast="mdx_vs_WT",design="~ condition",reference="WT",alpha=.05,
                minimum_count=10,minimum_samples=3,genes_tested=nrow(dds),degs=sum(significant),up=sum(significant&res$log2FoldChange>0),
                down=sum(significant&res$log2FoldChange<0),n_samples=nrow(meta),groups=as.list(table(meta$condition)),
                p_adjust="BH",independent_filtering=TRUE,filter_threshold=unname(metadata(res)$filterThreshold),
                outlier_replacement="DESeq2 default minReplicatesForReplace=7",outlier_replaced_genes=replaced,
                no_replacement_degs=sum(!is.na(no_replace$padj)&no_replace$padj<.05&abs(no_replace$log2FoldChange)>1),
                versions=list(R=R.version.string,DESeq2=as.character(packageVersion("DESeq2")),apeglm=as.character(packageVersion("apeglm"))))
write_json(summary,file.path(out,"summary.json"),pretty=TRUE,auto_unbox=TRUE)
print(summary)
