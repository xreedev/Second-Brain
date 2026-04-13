from arxiv_parser import parse_arxiv

# From a local PDF
xml  = parse_arxiv("paper/test.pdf", output_format="xml")

print(xml)
