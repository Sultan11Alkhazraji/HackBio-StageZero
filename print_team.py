#!/usr/bin/env python3
"""
Print a short summary for every team member:
 * reads the CSV (now with GitHub & LinkedIn placeholders)
 * extracts NCBI accession + optional start/end from each URL,
 * downloads the FASTA via Entrez,
 * prints DNA preview, GC-content, and the GitHub/LinkedIn info.
"""
# (if need be install the dependencies) !pip install biopython pandas
# -------------------------------------------------
# Imports
# -------------------------------------------------
import re
from urllib.parse import urlparse, parse_qs

import pandas as pd
from Bio import Entrez, SeqIO    # <-- talk to NCBI and parse FASTA

# -------------------------------------------------
# Global variables for NCBI email
# -------------------------------------------------
Entrez.email = "hackbio@example.com"   # <-- email for NCBI access

# -------------------------------------------------
# Read CSV data
# -------------------------------------------------
def read_csv_data(filename):
    """
    Reads team.csv file and returns a DataFrame.
    Handles missing or malformed columns.
    """
    try:
        df = pd.read_csv(filename)
        return df
    except Exception as e:
        print(f"⚠️  Error reading CSV file '{filename}': {e}")
        return None

# -------------------------------------------------
# Parse NCBI URL
# -------------------------------------------------
def parse_url(url):
    """
    Returns (accession, start, end)
    * accession – e.g. 'NC_000010.11'
    * start / end – ints if ?from=…&to=…, otherwise None
    """
    m = re.search(r"/nuccore/([^?]+)", url)
    accession = m.group(1) if m else None

    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    start = int(qs["from"][0]) if "from" in qs else None
    end   = int(qs["to"][0])   if "to" in qs else None
    return accession, start, end

# -------------------------------------------------
# Fetch DNA sequence from NCBI
# -------------------------------------------------
def fetch_dna_sequence(accession, start=None, end=None):
    """
    Downloads DNA sequence using Entrez.
    Returns SeqRecord object or None if failed.
    """
    try:
        fetch_args = {
            "db": "nuccore",
            "id": accession,
            "rettype": "fasta",
            "retmode": "text"
        }
        if start is not None and end is not None:
            fetch_args["seq_start"] = start
            fetch_args["seq_stop"]  = end

        with Entrez.efetch(**fetch_args) as handle:
            seq_record = SeqIO.read(handle, "fasta")
        return seq_record
    except Exception as e:
        print("⚠️  Error while fetching DNA sequence:")
        print(f"   {e}")
        return None

# -------------------------------------------------
# Calculate GC content
# -------------------------------------------------
def gc_content(seq_str):
    """
    Calculates GC content percentage from a sequence string.
    Returns float or 0.0 if empty.
    """
    seq = seq_str.upper()
    if len(seq) == 0:
        return 0.0
    g = seq.count('G')
    c = seq.count('C')
    return ((g + c) / len(seq)) * 100

# -------------------------------------------------
# Print team member summary
# -------------------------------------------------
def print_summary(name, username, country, hobby, affil, url,
                  github_url, linkedin_url):
    """
    Prints a summary of one team member.
    """
    print("=" * 70)
    print(f"Name        : {name}")
    print(f"Slack user  : {username}")
    print(f"Country     : {country}")
    print(f"Hobby       : {hobby}")
    print(f"Affiliations: {affil}")
    print()

    # Print URLs
    print(f"GitHub URL   : {github_url or 'N/A'}")
    print(f"LinkedIn URL : {linkedin_url or 'N/A'}")

    print()

# -------------------------------------------------
# Process single team member
# -------------------------------------------------
def process_team_member(df, i):
    """
    Processes one team member from DataFrame.
    Returns True if success, False if failure.
    """
    # Read static fields
    name        = df.loc[i, "name"]
    username    = df.loc[i, "username"]
    country     = df.loc[i, "country"]
    hobby       = df.loc[i, "hobby"]
    affil       = df.loc[i, "affiliations"]
    url         = df.loc[i, "url"]

    # Read GitHub/LinkedIn fields
    github_url   = df.loc[i, "github_url"] if "github_url" in df.columns else ""
    linkedin_url = df.loc[i, "linkedin_url"] if "linkedin_url" in df.columns else ""

    print_summary(name, username, country, hobby, affil, url,
                  github_url, linkedin_url)

    # Extract accession
    acc, start, end = parse_url(url)

    if not acc:
        print("⚠️  Could not find an accession in the URL – skipping DNA fetch.")
        return False

    # Fetch DNA sequence
    seq_record = fetch_dna_sequence(acc, start, end)

    if seq_record is None:
        return False

    # Print preview
    preview_len = 60
    dna_str = str(seq_record.seq)

    print("DNA (FASTA header) :", seq_record.id)
    print(f"Length               : {len(dna_str)} bp")
    print("First {} bases       :".format(preview_len))
    print(dna_str[:preview_len] + ("…" if len(dna_str) > preview_len else ""))

    # Calculate and print GC content
    gc_pct = gc_content(dna_str)
    print(f"GC content           : {gc_pct:.2f}%")

    # Add extra spacing between members
    print("\n" + "="*70)
    print()

    return True

# -------------------------------------------------
# Main execution loop
# -------------------------------------------------
def main():
    """
    Main function that reads CSV and processes each team member.
    """
    df = read_csv_data("team.csv")
    if df is None:
        return

    print("=" * 70)
    print(f"📊 Processing {len(df)} team members...")
    print("=" * 70)

    for i in range(len(df)):
        print(f"Processing member {i+1} of {len(df)}:")
        process_team_member(df, i)

if __name__ == "__main__":
    main()
