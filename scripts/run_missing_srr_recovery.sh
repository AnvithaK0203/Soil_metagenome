#!/usr/bin/env bash
set -euo pipefail
missing=(SRR33963318 SRR33963319 SRR33963320 SRR33963321 SRR33963322 SRR33963323 SRR33963324 SRR5365029 SRR8468865 SRR9093167 SRR9830591)
for srr in "${missing[@]}"; do
  echo "Recovering ${srr}"
  prefetch "${srr}" -O sra
  fasterq-dump "sra/${srr}/${srr}.sra" -O raw_fastq --split-files -e 4 --temp tmp_sra
  pigz -f raw_fastq/${srr}*.fastq
  kraken2 --db kraken_db/minikraken2_v2_8GB_201904_UPDATE --threads 2 --paired raw_fastq/${srr}_1.fastq.gz raw_fastq/${srr}_2.fastq.gz --report kraken_out/${srr}.report --output kraken_out/${srr}.kraken
done
