# Welcome to ChemGraphBuilder

The `chemgraphbuilder` package is a specialized tool designed for researchers in bioinformatics, cheminformatics, and computational biology. It enables the construction of detailed knowledge graphs that map the complex interactions between chemical compounds, genes, proteins, and bioassays. These knowledge graphs are critical for visualizing and understanding the multifaceted relationships in biochemical networks.

At its core, `chemgraphbuilder` integrates data from PubChem and utilize Neo4j, creating nodes that represent key entities such as compounds, genes, proteins, and bioassays. It further enriches these graphs by incorporating various relationships, including:

- **BioAssay-Compound Relationships**: Capturing the interactions where bioassays evaluate the effects of specific compounds. This is crucial for understanding the efficacy and mechanism of action of pharmaceuticals.
- **BioAssay-Gene Relationships**: Documenting instances where bioassays study specific genes, providing valuable data on gene function and regulation.
- **Gene-Protein Relationships**: Mapping the connections where genes encode proteins, providing insights into genetic regulation and protein function.
- **Compound-Gene Interactions**: Detailing how compounds interact with genes, categorized into various interaction types such as Inhibitors, Inactivators, Activators, Inducers, Substrates, Ligands, and Inactive compounds. This classification aids in understanding gene regulation, drug mechanisms, and potential therapeutic applications.
- **Compound Similarities**: Highlighting chemical similarities between compounds, which can suggest similar biological activities or shared molecular properties.
- **Compound Co-occurrence**: Identifying instances where compounds or genes co-occur in scientific literature, indicating potential interactions or co-regulation.

This comprehensive approach allows researchers to explore and analyze data across multiple levels of biological organization, from molecular interactions to broader biological pathways. The insights gained from these knowledge graphs can drive innovation in drug discovery, toxicology, and personalized medicine by revealing new drug targets, understanding adverse drug reactions, and exploring the molecular basis of diseases.

---

The `chemgraphbuilder` package is versatile and can be utilized both in Python code and via the command line interface. For practical examples and use cases, please refer to the "Usage Examples" section available in the menu on the left sidebar. For comprehensive documentation of the main classes and their functionalities, visit [the Documentation Page](https://asmaa-a-abdelwahab.github.io/ChemGraphBuilder/documentation/).

---

## Installation:

You can visit this page to get the installation command: [PyPI Project Page](https://test.pypi.org/project/chemgraphbuilder)
```sh
!pip install -i https://test.pypi.org/simple/ chemgraphbuilder==1.14.0
```

## Project layout

    chemgraphbuilder/                 # Main source code directory for the chemgraphbuilder package.
    build/
        lib/chemgraphbuilder/         # Build artifacts and main package files.
    chemgraphbuilder.egg-info/        # Package metadata and distribution information.
    dist/                             # Distribution packages (.tar.gz, .whl).
    docs/                             # Documentation files for the project.
        index.md                      # Documentation homepage.
        ...                           # Other markdown pages, images, and files.
    examples/                         # Example scripts and usage demonstrations.
    __pycache__/                      # Compiled Python bytecode files.
    .gitignore                        # Specifies files and directories to be ignored by Git.
    LICENSE                           # License file detailing the terms of use.
    README.md                         # Project overview and instructions.
    mkdocs.yml                        # Configuration file for MkDocs.
    requirements.txt                  # List of Python dependencies for the project.
    setup.py                          # Setup script for packaging and distribution.
            
## Gallery

Welcome to the gallery. Here are some screenshots from the Knowledge Graph built using this package:

<div id="carouselExample" class="carousel slide" data-ride="carousel">
  <div class="carousel-inner">
    <div class="carousel-item active">
      <img src="./assets/images/schema.png" class="d-block w-100" alt="First slide">
    </div>
    <div class="carousel-item">
      <img src="./assets/images/1.png" class="d-block w-100" alt="First slide">
    </div>
    <div class="carousel-item">
      <img src="./assets/images/2.png" class="d-block w-100" alt="Second slide">
    </div>
    <div class="carousel-item">
      <img src="./assets/images/3.png" class="d-block w-100" alt="Third slide">
    </div>
    <div class="carousel-item">
      <img src="./assets/images/4.png" class="d-block w-100" alt="Third slide">
    </div>
    <div class="carousel-item">
      <img src="./assets/images/5.png" class="d-block w-100" alt="Third slide">
    </div>
  </div>
  <a class="carousel-control-prev" href="#carouselExample" role="button" data-slide="prev">
    <span class="carousel-control-prev-icon" aria-hidden="true"></span>
    <span class="sr-only">Previous</span>
  </a>
  <a class="carousel-control-next" href="#carouselExample" role="button" data-slide="next">
    <span class="carousel-control-next-icon" aria-hidden="true"></span>
    <span class="sr-only">Next</span>
  </a>
</div>

