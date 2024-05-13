#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = TRUE)
file_name <- args[1]
# print(file_name)

source("input.R")
source("klink-2.R")

run_all(file_name)
klink2(file_name)
export_triples(file_name)
