# Using the skill

Install this entire folder in your agent's supported skill directory, or ask an agent with local file access to read [SKILL.md](SKILL.md) directly. Repository installation and dependency instructions are in the [project README](https://github.com/CEvildreaming/-schematic-deep-review#readme).

Provide the original schematic and ask:

```text
Use $schematic-deep-review to analyze the attached original schematic.
Explain the board's functions, every component's role and interactions,
and the complete power path. Download matching official datasheets,
show calculations with assumptions, and produce readable complete-page
annotated PDFs. Save the results in ./review-output and explain them in English.
```

Change the output language and directory as needed. Include the intended supply, load scenarios, BOM, netlist, exact part numbers, and PCB if available. These strengthen conclusions but do not block unrelated work. A previous annotated drawing may guide visual style; connections and electrical claims must be verified again from the original source.

Start reading the resulting **annotated schematic** and **power explanation**. Datasheets and excerpts provide supporting evidence; calculations and QA records make the work traceable. They should not be prerequisites for understanding the main explanation.

The [standalone method](references/workflow.md) is readable without a particular AI product. The [knowledge index](knowledge/index.md) provides general circuit concepts and worked examples; device-specific requirements still come from matching manufacturer documents.

Original skill code and documentation are provided under the [MIT License](LICENSE). External documents, fonts, and dependencies retain their own terms; see [Third-party notices](https://github.com/CEvildreaming/-schematic-deep-review/blob/main/THIRD_PARTY_NOTICES.md).
