#!/usr/bin/env python3
"""
Dr. Islam Akef Ebeid - Normalized Project Backbone Schema Builder (Phase 1)
Creates the normalized `projects`, `project_artifacts`, `project_publications`,
`project_tags`, and `project_courses` subschema inside data/content.db and populates
atomic, non-duplicated project records extracted from CV, documents, code, data,
videos, publications, and portfolio pages.
"""

import json
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "content.db"


def get_doc_id_map(cur):
    cur.execute("SELECT id, filename FROM documents")
    return {row[1]: row[0] for row in cur.fetchall()}


def ensure_schema(cur):
    cur.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        tagline TEXT,
        short_summary TEXT NOT NULL,
        full_description TEXT,
        category TEXT NOT NULL,
        domain_stage TEXT DEFAULT 'foundational',
        status TEXT DEFAULT 'Published',
        year_start INTEGER,
        year_end INTEGER,
        institution_or_org TEXT,
        grant_award TEXT,
        tech_stack TEXT,
        code_snippet TEXT,
        license_model TEXT,
        price_display TEXT,
        storefront_category TEXT,
        is_featured INTEGER DEFAULT 0,
        is_storefront INTEGER DEFAULT 0,
        is_public INTEGER DEFAULT 1,
        display_order INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS project_artifacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        artifact_type TEXT NOT NULL,
        label TEXT NOT NULL,
        url_or_rel_path TEXT NOT NULL,
        format_badge TEXT,
        document_id INTEGER REFERENCES documents(id) ON DELETE SET NULL,
        display_order INTEGER DEFAULT 0,
        UNIQUE(project_id, artifact_type, url_or_rel_path)
    );

    CREATE TABLE IF NOT EXISTS project_publications (
        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        publication_id INTEGER NOT NULL REFERENCES publications(id) ON DELETE CASCADE,
        PRIMARY KEY (project_id, publication_id)
    );

    CREATE TABLE IF NOT EXISTS project_tags (
        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        tag TEXT NOT NULL,
        PRIMARY KEY (project_id, tag)
    );

    CREATE TABLE IF NOT EXISTS project_courses (
        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
        PRIMARY KEY (project_id, course_id)
    );
    """)


PROJECTS = [
    {
        "slug": "protgram-directgcn",
        "title": "ProtGram-DirectGCN",
        "tagline": "Directed Graph Convolutional Networks on Dense Residue Transition Graphs for PPI Prediction",
        "short_summary": "End-to-end deep learning pipeline inferring global dense residue transition graphs from primary protein sequences via hierarchical n-gram tokenization for directed GCN interaction prediction.",
        "full_description": "Translates protein amino acid sequences directly into weighted, directed n-gram transition graphs, enabling Directed Graph Convolutional Networks (Dir-GCN) to predict protein-protein interactions (PPI) across species with strong generalization and physical interpretability without requiring 3D structures.",
        "category": "AI & Life Sciences",
        "domain_stage": "02_ai_modeling",
        "status": "Published",
        "year_start": 2023,
        "year_end": 2025,
        "institution_or_org": "Texas Woman's University (Data2AI4LifeSciences Lab)",
        "grant_award": "TWU Startup Fund ($66K)",
        "tech_stack": ["Python", "PyTorch", "PyG / Dir-GCN", "Bioinformatics"],
        "code_snippet": "from protgram import DirectGCNModel\nmodel = DirectGCNModel(ngram=3, directed=True)\nprob = model.predict_ppi(seq_a, seq_b)",
        "license_model": "Dual-Licensed: AGPLv3 / Proprietary Commercial",
        "price_display": "Custom Seat / Enterprise",
        "storefront_category": "MODELING_ENGINES",
        "is_featured": 1,
        "is_storefront": 1,
        "display_order": 1,
        "tags": ["Graph Neural Networks", "Proteomics", "PPI Prediction", "PyTorch", "Bioinformatics"],
        "artifacts": [
            ("source_zip", "DiGCN Implementation Archive", "code/DiGCN.zip", "ZIP", None),
            ("source_zip", "MultivariateGCN Benchmark Suite", "code/multivariategcn.zip", "ZIP", None),
            ("github_repo", "GitHub Organization", "https://github.com/iebeid", "GitHub", None),
        ],
        "pub_dois": ["10.3389/fbinf.2025.1651623"],
    },
    {
        "slug": "multimodal-med-seg",
        "title": "Multimodal Medical Image Segmentation & Auto-Prompting",
        "tagline": "Domain-Knowledge Auto-Prompting & Spatial Channel Attention for Clinical Imaging",
        "short_summary": "NSF CISE/CCF collaborative project ($600K total / $210K TWU) integrating domain knowledge graphs with foundation segmentation models and Spatially Localized Channel Attention (SLCA).",
        "full_description": "Collaborative research between Texas Woman's University and UT Rio Grande Valley developing automated textual auto-prompt generation grounded in biomedical domain knowledge alongside Spatially Localized Channel Attention (SLCA) over vision foundation models for medical image segmentation and classification.",
        "category": "AI & Life Sciences",
        "domain_stage": "02_ai_modeling",
        "status": "Active Research",
        "year_start": 2024,
        "year_end": 2028,
        "institution_or_org": "Texas Woman's University & UTRGV",
        "grant_award": "NSF CISE-MSI #2523786 ($600K Total / $210K TWU)",
        "tech_stack": ["Python", "PyTorch", "Foundation Models", "SLCA", "Vision-Language"],
        "code_snippet": None,
        "license_model": "Academic / NSF Open Science",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 1,
        "is_storefront": 0,
        "display_order": 2,
        "tags": ["NSF Grant", "Medical Imaging", "Foundation Models", "Neuro-Symbolic AI", "Data Quality"],
        "artifacts": [
            ("lab_portal", "Data2AI4LifeSciences Lab", "pages/research/lab.html", "Lab", None),
        ],
        "pub_dois": [],
        "pub_title_matches": ["Adapting a Segmentation Foundation Model"],
    },
    {
        "slug": "xlpm-visintx",
        "title": "XLPM & VisInt-X Proteomics Suite",
        "tagline": "Cross-Linking Mass Spectrometry Curation & Interactive 3D WebGL Protein-Contact Viewer",
        "short_summary": "End-to-end chemical cross-linking mass spectrometry (XL-MS) relational pipeline paired with a synchronized 3-tier D3.js contact heatmap/treemap and 3Dmol.js WebGL structural viewer.",
        "full_description": "Combines the X-Link Peptide Mapping (XLPM) analysis algorithm (15-table xlpmwebv1 MySQL/Perl pipeline with 5 ppm / 0.8 Da b/y ion matcher and 14N/15N isotope engine) with VisInt-X, an interactive browser application coupling protein-level heatmaps, peptide treemaps, residue contact maps, and 3D WebGL tertiary structures.",
        "category": "Bioinformatics & 3D Visualization",
        "domain_stage": "03_visualization_kpi",
        "status": "Commercial / Published",
        "year_start": 2015,
        "year_end": 2023,
        "institution_or_org": "UA Little Rock (EAC) & UAMS",
        "grant_award": "EAC / UAMS Collaborative Research",
        "tech_stack": ["JavaScript", "D3.js", "3Dmol.js", "WebGL", "Perl", "MySQL"],
        "code_snippet": "visintx.mountViewer({\n  pdbId: '1AON', heatmapLevel: 3,\n  sync3DContacts: true\n});",
        "license_model": "Dual-Licensed: AGPLv3 / Proprietary Commercial",
        "price_display": "Custom Seat / Enterprise",
        "storefront_category": "DATA_CURATION VISUALIZATION_REPORTING",
        "is_featured": 1,
        "is_storefront": 1,
        "display_order": 3,
        "tags": ["XL-MS", "Proteomics", "3D Visualization", "WebGL", "D3.js", "Interactive Demo"],
        "artifacts": [
            ("live_demo", "Launch Live Interactive 3D Viewer", "pages/research/xlpm/index.html", "Live WebGL", None),
            ("github_repo", "VisInt-X Repository", "https://github.com/iebeid/VisInt-X.git", "GitHub", None),
            ("video", "XLPM Action Demo Video", "videos/XLPM-Action.mp4", "MP4", None),
            ("video", "XLPM Demo Video (YouTube)", "https://www.youtube.com/watch?v=yVLHPw4s47k", "YouTube", None),
            ("video", "VisInt-X Walkthrough (YouTube)", "https://youtu.be/YdO3IQsTDq4", "YouTube", None),
            ("paper_pdf", "VisInt-X Research Paper", "documents/IAE_VISINTX.pdf", "PDF", "IAE_VISINTX.pdf"),
            ("paper_pdf", "XLPM SPIE/IS&T Paper", "documents/XLPM-SPIE-IST-submission.pdf", "PDF", "XLPM-SPIE-IST-submission.pdf"),
            ("paper_pdf", "XLPM Perception Manuscript", "documents/XLPM-SPIE-IST-Manuscript.pdf", "PDF", "XLPM-SPIE-IST-Manuscript.pdf"),
            ("paper_pdf", "XLPM Spatial Auto-Calibration", "documents/XLPM Map.pdf", "PDF", "XLPM Map.pdf"),
            ("paper_pdf", "XLPM Extended Abstract", "documents/xlpm-nofigures-final.pdf", "PDF", "xlpm-nofigures-final.pdf"),
            ("slides", "VisInt-X MCBIOS Presentation", "documents/visintx_presentation.pdf", "PDF", "visintx_presentation.pdf"),
            ("slides", "XLPM Map Viewer Deck", "documents/XLPM-Map-Viewer-Final.pptx", "PPTX", "XLPM-Map-Viewer-Final.pptx"),
        ],
        "pub_title_matches": ["XLPM: Cross-Linking Mass Spectrometry"],
    },
    {
        "slug": "xlpmol-viewer",
        "title": "XLPMOL: OpenGL Protein Model Viewer",
        "tagline": "Native Desktop 3D Molecular Interaction & Cross-Link Structure Visualizer",
        "short_summary": "Standalone C++/OpenGL desktop molecular structure and cross-linking mass spectrometry (CXMS) contact viewer with real-time residue highlighting.",
        "full_description": "Desktop molecular visualization companion to XLPM engineered in C++ and OpenGL for inspecting cross-linked peptide spectra mapped onto three-dimensional PDB protein geometries.",
        "category": "Bioinformatics & 3D Visualization",
        "domain_stage": "03_visualization_kpi",
        "status": "Published",
        "year_start": 2016,
        "year_end": 2022,
        "institution_or_org": "UA Little Rock (Emerging Analytics Center)",
        "grant_award": None,
        "tech_stack": ["C++", "OpenGL", "PDB / FASTA"],
        "code_snippet": None,
        "license_model": "Academic / Open Source",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 4,
        "tags": ["OpenGL", "C++", "Molecular Visualization", "Proteomics"],
        "artifacts": [
            ("github_repo", "XLPMOL Repository", "https://github.com/iebeid/xlpmol.git", "GitHub", None),
            ("paper_pdf", "XLPMol3DViewer Paper", "documents/XLPMol3DViewer.pdf", "PDF", "XLPMol3DViewer.pdf"),
        ],
        "pub_title_matches": ["XLPMol3DViewer"],
    },
    {
        "slug": "dataintegrationtoolkit",
        "title": "DataIntegrationToolkit (DITK)",
        "tagline": "Medallion Lakehouse & Generalized ML Data Preparation Pipeline",
        "short_summary": "Generalized Lakehouse and Data Preparation Engine (Bronze -> Silver -> Gold) with automated ingestion, fuzzy blocking, and scalable Entity Resolution prior to AI/ML modeling.",
        "full_description": "High-performance data engineering toolkit eliminating the pre-modeling bottleneck right before data scientists operate. Implements tiered Medallion Lakehouse storage, deterministic schema mapping, and scalable entity resolution generalized for any downstream machine learning or AI modeling pipeline.",
        "category": "Data Engineering & Entity Resolution",
        "domain_stage": "01_data_prep",
        "status": "Commercial / OSS",
        "year_start": 2023,
        "year_end": 2026,
        "institution_or_org": "Unity Systems",
        "grant_award": None,
        "tech_stack": ["Python", "Medallion Lakehouse", "Parquet", "Entity Resolution"],
        "code_snippet": "import dataintegrationtoolkit as ditk\nlake = ditk.Lakehouse('./lakehouse')\nclean = lake.prepare_ml_dataset('records.parquet')",
        "license_model": "Dual-Licensed: AGPLv3 / Proprietary Commercial",
        "price_display": "$999/dev seat",
        "storefront_category": "DATA_CURATION MODELING_ENGINES",
        "is_featured": 1,
        "is_storefront": 1,
        "display_order": 5,
        "tags": ["Data Engineering", "Medallion Lakehouse", "Entity Resolution", "Feature Prep", "ML Pipeline"],
        "artifacts": [
            ("github_repo", "DITK Repository", "https://github.com/iebeid/DataIntegrationToolkit", "GitHub", None),
        ],
    },
    {
        "slug": "ailifecyclekit",
        "title": "AILifecycleKit",
        "tagline": "Deterministic Dataset Lineage, Curation & Real-Time Tensor Drift SDK",
        "short_summary": "Lightweight Python SDK automating local dataset curation, deterministic lineage versioning, and real-time tensor drift evaluation across production AI pipelines.",
        "full_description": "Built for production ML engineering teams and ITIL-governed AI lifecycles to track training dataset provenance, detect feature/tensor distribution drift prior to inference degradation, and export reproducible lineage manifests.",
        "category": "Data Engineering & Entity Resolution",
        "domain_stage": "01_data_prep",
        "status": "Commercial / OSS",
        "year_start": 2024,
        "year_end": 2026,
        "institution_or_org": "Unity Systems",
        "grant_award": None,
        "tech_stack": ["Python", "Parquet", "Lineage", "Drift Detection"],
        "code_snippet": "import ailifecyclekit as alk\ntracker = alk.DriftTracker(baseline_dataset='v1_clean.parquet')\nanomalies = tracker.evaluate_stream(incoming_tensor, threshold=0.85)",
        "license_model": "Dual-Licensed: AGPLv3 / Proprietary Commercial",
        "price_display": "$499/dev seat",
        "storefront_category": "DATA_CURATION",
        "is_featured": 1,
        "is_storefront": 1,
        "display_order": 6,
        "tags": ["AI Lifecycle", "Data Quality", "Lineage", "Drift Detection", "Python SDK"],
        "artifacts": [
            ("pip_command", "PyPI Install Command", "pip install ailifecyclekit", "pip", None),
            ("github_repo", "Source Repository", "https://github.com/iebeid", "GitHub", None),
        ],
    },
    {
        "slug": "moder-grapher",
        "title": "ModER & ModER-GraphER",
        "tagline": "Unsupervised Graph-Based Entity Resolution via Composite Modularity Optimization & LSH",
        "short_summary": "Doctoral dissertation and unsupervised graph entity resolution engine combining Locality-Sensitive Hashing (LSH) with Composite Modularity Optimization to resolve ambiguous records.",
        "full_description": "Addresses identity ambiguity across heterogeneous data sources without labeled training pairs by constructing similarity graphs over blocked candidate pairs via LSH and partitioning clusters via composite graph modularity optimization. Also includes TransER (hierarchical record clustering).",
        "category": "Data Engineering & Entity Resolution",
        "domain_stage": "02_ai_modeling",
        "status": "Published / Commercial",
        "year_start": 2020,
        "year_end": 2025,
        "institution_or_org": "UA Little Rock & Unity Systems",
        "grant_award": "NSF Sponsored Ph.D. Research",
        "tech_stack": ["Python", "Graph ER", "LSH", "Modularity Optimization", "NLP"],
        "code_snippet": "from moder import GraphEREngine\ner = GraphEREngine(lsh_bands=16, resolution=1.0)\nclusters = er.resolve_entities(heterogeneous_records)",
        "license_model": "Dual-Licensed: AGPLv3 / Proprietary Commercial",
        "price_display": "Custom Seat / Enterprise",
        "storefront_category": "MODELING_ENGINES",
        "is_featured": 1,
        "is_storefront": 1,
        "display_order": 7,
        "tags": ["Entity Resolution", "Data Quality", "Graph Clustering", "LSH", "PhD Dissertation"],
        "artifacts": [
            ("publisher_url", "IJACSA Journal Paper", "https://doi.org/10.14569/IJACSA.2022.0130901", "DOI", None),
            ("publisher_url", "ITNG 2022 Springer Chapter (TransER)", "https://link.springer.com/chapter/10.1007/978-3-030-98974-5_8", "Springer", None),
            ("github_repo", "Source Registry", "https://github.com/iebeid", "GitHub", None),
        ],
        "pub_dois": ["10.21900/iconf.2019.103363"],
    },
    {
        "slug": "medgraph-pubmed-kg",
        "title": "PubMed Knowledge Graph & MedGraph",
        "tagline": "Semantic Biomedical Information Retrieval via Knowledge Graph Embeddings",
        "short_summary": "Integrates PubMed biomedical literature entities, NIH grants, and author disambiguation into a Knowledge Graph with Node2Vec embeddings for semantic literature search.",
        "full_description": "Constructed bio-entity knowledge graphs over millions of PubMed abstracts using fine-tuned BERT NER and author disambiguation (Scientific Data 2020), then engineered MedGraph—a semantic search and document-ranking engine using Node2Vec/Skip-gram graph embeddings (Frontiers in Big Data 2022).",
        "category": "AI & Life Sciences",
        "domain_stage": "02_ai_modeling",
        "status": "Published",
        "year_start": 2019,
        "year_end": 2022,
        "institution_or_org": "UT Austin & UA Little Rock",
        "grant_award": None,
        "tech_stack": ["Python", "Node2Vec", "BERT NER", "Knowledge Graphs", "Information Retrieval"],
        "code_snippet": None,
        "license_model": "Academic / Open Science",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 8,
        "tags": ["Knowledge Graphs", "PubMed", "Information Retrieval", "BERT", "Node2Vec"],
        "artifacts": [
            ("publisher_url", "MedGraph Paper (Frontiers in Big Data)", "https://doi.org/10.3389/fdata.2022.1028994", "DOI", None),
            ("publisher_url", "PubMed KG Paper (Nature Scientific Data)", "https://doi.org/10.1038/s41597-020-0583-0", "DOI", None),
            ("slides", "MedGraph MSc Defense Deck", "documents/MedGraph-Final-Presentation.pptx", "PPTX", "MedGraph-Final-Presentation.pptx"),
            ("paper_pdf", "KG Mining Qualifying Paper", "documents/UT-Qualifying-Paper.pdf", "PDF", "UT-Qualifying-Paper.pdf"),
        ],
    },
    {
        "slug": "chem2bio2rdf-drug-repurposing",
        "title": "Chem2Bio2RDF Knowledge Graph Drug-Target Prediction",
        "tagline": "Metapath2Vec, Edge2Vec & GraphSage Embeddings for Computational Drug Repurposing",
        "short_summary": "AbbVie & UT Austin collaboration evaluating heterogeneous graph embedding models across 30,000 compound-protein pairs extracted from Chem2Bio2RDF.",
        "full_description": "Systematically benchmarked Node2Vec, Edge2Vec, Metapath2Vec (49 biomedical metapaths), and GraphSage with Top-K similarity refinement for drug-target interaction and drug repurposing candidate prediction (iConference 2021).",
        "category": "AI & Life Sciences",
        "domain_stage": "02_ai_modeling",
        "status": "Published",
        "year_start": 2020,
        "year_end": 2021,
        "institution_or_org": "AbbVie Inc. & UT Austin",
        "grant_award": None,
        "tech_stack": ["Python", "Metapath2Vec", "GraphSage", "RDF / Chem2Bio2RDF", "Link Prediction"],
        "code_snippet": None,
        "license_model": "Academic",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 9,
        "tags": ["Drug Discovery", "Knowledge Graphs", "Chem2Bio2RDF", "AbbVie", "Metapath2Vec"],
        "artifacts": [
            ("poster", "KG Mining Poster (AbbVie 2020)", "documents/Bioinformatics_Poster_2020.pptx", "PPTX", "Bioinformatics_Poster_2020.pptx"),
        ],
    },
    {
        "slug": "covidnlpgraph",
        "title": "CovidNLPGraph & Scientometric Entity Networks",
        "tagline": "Open Biomedical Entity & Paper-Entity Citation Graph Dataset",
        "short_summary": "Extracted COVID-19 biomedical entities, MeSH/chemical relations, and citation network samples supporting Scientometrics & ACM KDD knowledge graph studies.",
        "full_description": "Provides open sample datasets and entity-metric citation networks uniting COVID-19 literature entities across drugs, diseases, genes, and authors for bibliometric and computational social science research (Scientometrics 2021/2022, KDD 2020).",
        "category": "Data Engineering & Entity Resolution",
        "domain_stage": "01_data_prep",
        "status": "Published Dataset",
        "year_start": 2020,
        "year_end": 2022,
        "institution_or_org": "UT Austin",
        "grant_award": None,
        "tech_stack": ["Python", "NLP", "Knowledge Graphs", "Scientometrics"],
        "code_snippet": None,
        "license_model": "Open Dataset",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 10,
        "tags": ["Open Dataset", "COVID-19", "NLP", "Scientometrics", "Knowledge Graphs"],
        "artifacts": [
            ("dataset", "CovidNLPGraph Sample Dataset (.zip)", "data/CovidNLPGraph_Sample.zip", "ZIP", None),
        ],
    },
    {
        "slug": "eyeadapt-gdwm",
        "title": "EyeArt / EyeAdapt Engine & GDWM",
        "tagline": "Real-Time Gaze Transition Entropy, Markov Cognitive Modeling & Adaptive UIs",
        "short_summary": "Eye-tracking & biometric cognitive-load engine using Bayesian mixed-effects Markov models and real-time gaze transition entropy, sponsored by Lockheed Martin (ACM ETRA Best Short Paper).",
        "full_description": "Includes real-time gaze entropy estimation, Bayesian semi-parametric mixed-effects Markov scanpath modeling, Gaze Directed Window Management (GDWM) simulation harness, and adaptive C4ISR UI prototypes developed at UT Austin.",
        "category": "Scientific Visualization & HCI",
        "domain_stage": "01_data_prep",
        "status": "Published / Commercial",
        "year_start": 2017,
        "year_end": 2020,
        "institution_or_org": "UT Austin & Lockheed Martin RMS",
        "grant_award": "Lockheed Martin Sponsored R&D",
        "tech_stack": ["Python", "PyTorch", "Eye Tracking", "Bayesian Markov Models", "OpenCV"],
        "code_snippet": "from eyeart import TelemetryStream\nstream = TelemetryStream(hz=120)\nentropy = stream.compute_transition_entropy()",
        "license_model": "Dual-Licensed: MIT / Proprietary Commercial",
        "price_display": "Custom Seat / Enterprise",
        "storefront_category": "DATA_CURATION",
        "is_featured": 1,
        "is_storefront": 1,
        "display_order": 11,
        "tags": ["Eye Tracking", "Cognitive Load", "HCI", "Bayesian Markov", "Best Paper Award"],
        "artifacts": [
            ("source_zip", "EyeAdaptEngine Source & Eval Suite (.zip)", "code/EyeAdaptEngine.zip", "ZIP", None),
            ("video", "Eye-Tracking Simulation Video", "videos/Eye-Tracking-Sim.mp4", "MP4", None),
            ("slides", "Lockheed Martin / UTA Eye-Tracking Deck", "documents/UTA-Eye-Tracking-2018.pptx", "PPTX", "UTA-Eye-Tracking-2018.pptx"),
            ("publisher_url", "ETRA 2019 Paper (Best Short Paper)", "https://doi.org/10.1145/3317956.3318151", "DOI", None),
            ("publisher_url", "ETRA 2018 Paper (Real-time Entropy)", "https://doi.org/10.1145/3204493.3208340", "DOI", None),
        ],
    },
    {
        "slug": "raymarchervr",
        "title": "RaymarcherVR Engine",
        "tagline": "Stereoscopic C++ / CUDA / OpenGL Direct Raymarching Shader Engine",
        "short_summary": "Ultra-low-latency C++ and GLSL/CUDA pipeline delivering direct stereoscopic raymarching shaders inside CAVE projection rooms, quad-buffered workstations, and HMDs.",
        "full_description": "Engineered for real-time volumetric and signed-distance-field rendering across synchronized multi-wall CAVE VR clusters and desktop stereo displays.",
        "category": "Scientific Visualization & HCI",
        "domain_stage": "03_visualization_kpi",
        "status": "Commercial / OSS",
        "year_start": 2015,
        "year_end": 2018,
        "institution_or_org": "UA Little Rock (EAC) & Unity Systems",
        "grant_award": None,
        "tech_stack": ["C++", "CUDA", "OpenGL", "GLSL", "VR / Stereo"],
        "code_snippet": "RaymarcherVR::Context ctx(StereoMode::QUAD_BUFFERED);\nctx.compileShader(\"volumetric_sdf.glsl\");\nctx.renderFrame();",
        "license_model": "Dual-Licensed: AGPLv3 / Proprietary Commercial",
        "price_display": "Custom Seat / Enterprise",
        "storefront_category": "VISUALIZATION_REPORTING",
        "is_featured": 0,
        "is_storefront": 1,
        "display_order": 12,
        "tags": ["VR", "Raymarching", "OpenGL", "CUDA", "C++", "Stereoscopic 3D"],
        "artifacts": [
            ("github_repo", "RaymarcherVR Repository", "https://github.com/iebeid/RaymarcherVR.git", "GitHub", None),
            ("github_repo", "Quad Buffered Stereo Repo", "https://github.com/iebeid/quad-buffered-stereo.git", "GitHub", None),
            ("github_repo", "DICOM to Isosurface Repo", "https://github.com/iebeid/dicom-to-isosurface.git", "GitHub", None),
        ],
    },
    {
        "slug": "cudaparticles",
        "title": "CudaParticles Engine",
        "tagline": "Zero-Copy Multi-Million Particle Simulation & GPU Rendering Engine",
        "short_summary": "High-performance particle physics framework offloading multi-million point array computations to NVIDIA CUDA cores with zero-copy OpenGL interop rendering.",
        "full_description": "Parallel GPU compute engine written in C++, CUDA, and OpenGL using shared VBO memory buffers for interactive fluid, molecular, and astrophysics particle simulations.",
        "category": "Scientific Visualization & HCI",
        "domain_stage": "03_visualization_kpi",
        "status": "Commercial / OSS",
        "year_start": 2015,
        "year_end": 2017,
        "institution_or_org": "UA Little Rock (EAC) & Unity Systems",
        "grant_award": None,
        "tech_stack": ["C++", "CUDA", "OpenGL", "GPU Interop"],
        "code_snippet": "CudaParticleSystem sys(2_000_000);\nsys.stepPhysicsCUDA(dt);\nsys.renderZeroCopyGL();",
        "license_model": "Dual-Licensed: AGPLv3 / Proprietary Commercial",
        "price_display": "Custom Seat / Enterprise",
        "storefront_category": "VISUALIZATION_REPORTING",
        "is_featured": 0,
        "is_storefront": 1,
        "display_order": 13,
        "tags": ["CUDA", "GPU Compute", "OpenGL", "Particle Simulation", "C++"],
        "artifacts": [
            ("github_repo", "CudaParticles Repository", "https://github.com/iebeid/cuda-particles.git", "GitHub", None),
        ],
    },
    {
        "slug": "cave-realtime-scanner",
        "title": "CAVE Real-Time 3D Object Scanner & Sensor Tracking",
        "tagline": "Intel RealSense RGB-D Turntable Mesh Reconstruction & CAVE Manipulation",
        "short_summary": "Real-time RGB-D object scanning, Marching Cubes mesh generation, and Leap Motion / Kinect gesture interaction inside a cluster-driven VR-Juggler CAVE.",
        "full_description": "Combines Intel RealSense depth cameras, custom turntable scanning, Visual SLAM GPU tracking, and VR-Juggler C++ stereo rendering to capture physical objects and manipulate their 3D meshes interactively inside immersive CAVE rooms.",
        "category": "Scientific Visualization & HCI",
        "domain_stage": "03_visualization_kpi",
        "status": "Published",
        "year_start": 2015,
        "year_end": 2018,
        "institution_or_org": "UA Little Rock (EAC) & TACC / Intel",
        "grant_award": "ACM ETRA / VR-Juggler Project",
        "tech_stack": ["C++", "Intel RealSense SDK", "VR-Juggler", "OpenGL", "Leap Motion", "Kinect"],
        "code_snippet": None,
        "license_model": "Academic / Open Source",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 14,
        "tags": ["CAVE VR", "3D Scanning", "Intel RealSense", "SLAM", "VR-Juggler", "Leap Motion"],
        "artifacts": [
            ("paper_pdf", "CAVE Real-Time Scanner Paper", "documents/vr-project-final-paper.pdf", "PDF", "vr-project-final-paper.pdf"),
            ("paper_pdf", "Scanner Technical Report", "documents/Real.pdf", "PDF", "Real.pdf"),
            ("paper_pdf", "VR Project Proposal", "documents/vr-project-proposal.pdf", "PDF", "vr-project-proposal.pdf"),
            ("video", "CAVE-in-a-Box VR Demo", "videos/CaveInABox.webm", "WebM", None),
            ("video", "RealSense Turntable Demo (YouTube)", "https://youtu.be/TkIpVOf5Kmc", "YouTube", None),
            ("github_repo", "Real-time CAVE Scanner Repo", "https://github.com/iebeid/realtime-cave-scanner.git", "GitHub", None),
            ("github_repo", "RealSense CM VIVE SLAM Repo", "https://github.com/iebeid/RealSense_CM_VIVE_SLAM.git", "GitHub", None),
            ("github_repo", "RealSense Tracking Repo", "https://github.com/iebeid/realsense-tracking.git", "GitHub", None),
            ("github_repo", "CAVE LeapMotion Repo", "https://github.com/iebeid/cave-leapmotion.git", "GitHub", None),
            ("github_repo", "CAVE VR-Juggler Interactivity", "https://github.com/iebeid/cave-vrjuggler-interactivity.git", "GitHub", None),
            ("github_repo", "CAVE Point Cloud Viewer", "https://github.com/iebeid/cave-vrjuggler-pointcloud-viewer.git", "GitHub", None),
        ],
        "pub_dois": ["10.1145/3314111.3319832"],
    },
    {
        "slug": "cluster-webgl-earthviz",
        "title": "ClusterWebGL, EarthViz & CAVE Geovisualization",
        "tagline": "Synchronized Multi-View WebGL Tiled Walls & Geospatial Visualization",
        "short_summary": "Synchronized cluster WebGL rendering for high-resolution tiled display walls alongside EarthViz KML geospatial analytics and Google Earth / Photosphere CAVE viewers.",
        "full_description": "Spanning synchronized camera transforms across tiled wall displays using WebGL/Three.js, KML-driven geographic store & supply-chain telemetry (EarthViz), and immersive Google Earth CAVE environments.",
        "category": "Scientific Visualization & HCI",
        "domain_stage": "03_visualization_kpi",
        "status": "Published",
        "year_start": 2014,
        "year_end": 2018,
        "institution_or_org": "UA Little Rock (EAC) & UT Austin (TACC)",
        "grant_award": None,
        "tech_stack": ["WebGL", "Three.js", "Python", "KML", "Unity", "OpenGL"],
        "code_snippet": None,
        "license_model": "Academic / Open Source",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 15,
        "tags": ["WebGL", "Tiled Display Wall", "Geovisualization", "KML", "Unity VR"],
        "artifacts": [
            ("source_zip", "EarthViz Source Archive (.zip)", "code/EarthViz.zip", "ZIP", None),
            ("video", "Retail Geography Visualization Demo", "videos/Walmart-Vis.webm", "WebM", None),
            ("github_repo", "Cluster WebGL Repo", "https://github.com/iebeid/cluster-webgl.git", "GitHub", None),
            ("github_repo", "CAVE Google Earth Repo", "https://github.com/iebeid/cave-google-earth.git", "GitHub", None),
            ("github_repo", "Photo-sphere CAVE Viewer Repo", "https://github.com/iebeid/Photo-sphere-CAVE-Viewer.git", "GitHub", None),
            ("github_repo", "Info-Viz Unity VR Repo", "https://github.com/iebeid/info-viz-unity.git", "GitHub", None),
        ],
    },
    {
        "slug": "lda-topic-modeling",
        "title": "LDA Topic Modeling: Mallet vs. Gensim Benchmark",
        "tagline": "Empirical Evaluation of Latent Dirichlet Allocation Frameworks on 20 Newsgroups",
        "short_summary": "Comparative study of Mallet and Gensim LDA topic modeling pipelines across preprocessing, stop-word tuning, topic coherence, and execution speed.",
        "full_description": "Evaluates statistical word co-occurrence topic extraction using Latent Dirichlet Allocation (LDA) across 20,000 Usenet documents (20 Newsgroups corpus), comparing Java Mallet Gibbs sampling against Python Gensim.",
        "category": "Data Engineering & Entity Resolution",
        "domain_stage": "01_data_prep",
        "status": "Published Report",
        "year_start": 2016,
        "year_end": 2016,
        "institution_or_org": "UA Little Rock",
        "grant_award": None,
        "tech_stack": ["Python", "Gensim", "Mallet", "LDA", "NLP"],
        "code_snippet": None,
        "license_model": "Open Source",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 16,
        "tags": ["Topic Modeling", "LDA", "NLP", "Gensim", "Mallet"],
        "artifacts": [
            ("paper_pdf", "Final Benchmark Report", "documents/FinalReportInfoSci.pdf", "PDF", "FinalReportInfoSci.pdf"),
            ("github_repo", "Gensim Topic Modelling Repo", "https://github.com/iebeid/gensim-topic-modelling.git", "GitHub", None),
        ],
    },
    {
        "slug": "healthcare-data-governance",
        "title": "Healthcare Big Data Governance & National Lab IT Security Policy",
        "tagline": "Information Quality Governance, E-Discovery & Laboratory Security Frameworks",
        "short_summary": "Architectural frameworks for clinical Big Data governance alongside formal IT Security Policies, Data Stewardship, and E-Discovery standards for research laboratories.",
        "full_description": "Combines graduate research on Healthcare Information Systems governance (clinical, billing, EHR data stewardship) with formal security policy engineering authored for the National Visualization Laboratory.",
        "category": "Data Engineering & Entity Resolution",
        "domain_stage": "01_data_prep",
        "status": "Published Report",
        "year_start": 2014,
        "year_end": 2016,
        "institution_or_org": "UA Little Rock",
        "grant_award": None,
        "tech_stack": ["Information Governance", "ITIL", "HIPAA / Security Policies", "Data Quality"],
        "code_snippet": None,
        "license_model": "Academic",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 17,
        "tags": ["Data Governance", "IT Security", "ITIL", "Healthcare Systems", "E-Discovery"],
        "artifacts": [
            ("paper_pdf", "Healthcare Big Data Governance Paper", "documents/Ebeid_Final_Paper.pdf", "PDF", "Ebeid_Final_Paper.pdf"),
            ("paper_pdf", "National Visualization Lab Security Policies", "documents/The-National-Visualization-Lab.pdf", "PDF", "The-National-Visualization-Lab.pdf"),
            ("paper_pdf", "IT Security & E-Discovery Policies", "documents/IT Policies.pdf", "PDF", "IT Policies.pdf"),
            ("github_repo", "Data Governance Repo", "https://github.com/iebeid/data-governance.git", "GitHub", None),
            ("github_repo", "Data Security Repo", "https://github.com/iebeid/data-security.git", "GitHub", None),
        ],
    },
    {
        "slug": "smart-promotion-tool",
        "title": "Smart Promotion Tool (Smart Promo / SPT)",
        "tagline": "Enterprise Telecom Campaign Automation & Tariff Rule Engine",
        "short_summary": "Commercial campaign configuration and promotion engine built for Maroc Telecom to slash time-to-market for subscriber promotional tariffs and billing rules.",
        "full_description": "Engineered during telecom consulting delivery to replace error-prone manual billing configuration with an automated rule validation, promotion templating, and campaign deployment suite.",
        "category": "Industry & Enterprise Systems",
        "domain_stage": "01_data_prep",
        "status": "Production Delivered",
        "year_start": 2010,
        "year_end": 2011,
        "institution_or_org": "Maroc Telecom / Telecom Delivery",
        "grant_award": None,
        "tech_stack": ["Java", "Enterprise Billing", "BSCS", "SQL"],
        "code_snippet": None,
        "license_model": "Enterprise Consulting Case Study",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 18,
        "tags": ["Telecom", "Enterprise Software", "Billing Systems", "Maroc Telecom"],
        "artifacts": [
            ("paper_pdf", "Smart Promotion Tool Portfolio Spec", "documents/Smart Promotion Tool.pdf", "PDF", "Smart Promotion Tool.pdf"),
            ("github_repo", "Smart Promotion Tool Repo", "https://github.com/iebeid/smart-promotion-tool.git", "GitHub", None),
        ],
    },
    {
        "slug": "contract-print-bscs",
        "title": "Contract Print Suite & BSCS iX R2 Billing Migration",
        "tagline": "Automated Subscriber Contract Rendering & Telecom Billing UAT (Tunisie Telecom)",
        "short_summary": "Enterprise billing contract printing application (Impression Contrat Client) and BSCS iX R2 migration UAT suite delivered for Tunisie Telecom & telecom carriers.",
        "full_description": "Delivered bilingual French/Arabic commercial contract generation and high-volume telecom billing User Acceptance Testing (UAT) alongside RAID Revenue Assurance and EAI WebMethods integrations.",
        "category": "Industry & Enterprise Systems",
        "domain_stage": "03_visualization_kpi",
        "status": "Production Delivered",
        "year_start": 2009,
        "year_end": 2011,
        "institution_or_org": "Tunisie Telecom / Orange / WeDo Technologies",
        "grant_award": None,
        "tech_stack": ["Java", "WebMethods EAI", "Oracle SQL", "BSCS iX R2", "RAID"],
        "code_snippet": None,
        "license_model": "Enterprise Consulting Case Study",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 19,
        "tags": ["Tunisie Telecom", "BSCS", "Revenue Assurance", "EAI", "Enterprise"],
        "artifacts": [
            ("paper_pdf", "User Guide (French Edition)", "documents/Application_du_contrat_d_impression_guide_de_l_utilisateur.pdf", "PDF", "Application_du_contrat_d_impression_guide_de_l_utilisateur.pdf"),
            ("github_repo", "Contract Print Layout Repo", "https://github.com/iebeid/contract-print-layout.git", "GitHub", None),
            ("github_repo", "BSCS Migration Repo", "https://github.com/iebeid/bscs-migration.git", "GitHub", None),
            ("github_repo", "WebMethods EAI Suite Repo", "https://github.com/iebeid/webmethods.git", "GitHub", None),
            ("github_repo", "RAID Revenue Assurance Tutorial", "https://github.com/iebeid/raid-tutorial.git", "GitHub", None),
        ],
    },
    {
        "slug": "arkansas-gov-enterprise-suite",
        "title": "Arkansas.gov Civic Portal & Enterprise Data Warehousing Suite",
        "tagline": "State Government Web Services, OLAP Data Warehousing & Review Workflows",
        "short_summary": "Public-sector software engineering for Arkansas.gov (INA/NIC) alongside OLAP Retail Data Warehouses, HR management, inventory systems, and conference paper review platforms.",
        "full_description": "Covers full-stack web engineering for the State of Arkansas Information Network (INA) plus enterprise data warehouse modeling (Pet Store OLAP), Smart-HRM, Jupiter Inventory, CIS Department database, GA Timesheets, and academic peer-review web applications.",
        "category": "Industry & Enterprise Systems",
        "domain_stage": "01_data_prep",
        "status": "Production / Archived",
        "year_start": 2011,
        "year_end": 2014,
        "institution_or_org": "Information Network of Arkansas (Arkansas.gov) & ATU",
        "grant_award": None,
        "tech_stack": ["Java", "C#", "PHP", "SQL / OLAP", "Web Engineering"],
        "code_snippet": None,
        "license_model": "Open Source / Portfolio",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 20,
        "tags": ["Government", "Arkansas.gov", "Data Warehousing", "Full-Stack", "Databases"],
        "artifacts": [
            ("github_repo", "Information Network of Arkansas Repo", "https://github.com/iebeid/information-network-of-arkansas.git", "GitHub", None),
            ("github_repo", "PetStore Data Warehouse Repo", "https://github.com/iebeid/petstore-dataware-house.git", "GitHub", None),
            ("github_repo", "Paper Submission & Review App Repo", "https://github.com/iebeid/paper-submission-application.git", "GitHub", None),
            ("github_repo", "Smart-HRM Repo", "https://github.com/iebeid/human-resources-management-tool.git", "GitHub", None),
            ("github_repo", "Jupiter Inventory System Repo", "https://github.com/iebeid/jupiter-inventory-system.git", "GitHub", None),
            ("design_doc", "Paper Review System Design Doc", "documents/design-document.pdf", "PDF", "design-document.pdf"),
            ("design_doc", "GA Timesheets System Spec", "documents/GA_timesheets.pdf", "PDF", "GA_timesheets.pdf"),
            ("design_doc", "TakolEih Dining Guide Spec", "documents/takol-eh.pdf", "PDF", "takol-eh.pdf"),
        ],
    },
    {
        "slug": "genesis-gde",
        "title": "Genesis Development Environment (GDE)",
        "tagline": "MSc Thesis: Visual Drag-and-Drop Programming IDE & Algorithm Animator",
        "short_summary": "Master's thesis engineering a JavaFX integrated development environment enabling bidirectional translation between visual drag-and-drop list objects and Genesis runtime code.",
        "full_description": "Designed to help novice CS students visualize live data structures (nested heterogeneous lists) and bidirectional execution: dragging graphical sticky notes generates live Genesis source code, while code execution animates memory state transitions in JavaFX.",
        "category": "Legacy & Foundational Systems",
        "domain_stage": "foundational",
        "status": "MSc Thesis (Completed)",
        "year_start": 2012,
        "year_end": 2013,
        "institution_or_org": "Arkansas Tech University",
        "grant_award": None,
        "tech_stack": ["Java", "JavaFX 2.0", "Compilers / AST", "Algorithm Visualization"],
        "code_snippet": None,
        "license_model": "Academic Thesis",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 21,
        "tags": ["Visual Programming", "JavaFX", "CS Education", "MSc Thesis", "Algorithms"],
        "artifacts": [
            ("design_doc", "GDE Software Design Document", "documents/Genesis Development Environment Design Document.pdf", "PDF", "Genesis Development Environment Design Document.pdf"),
            ("paper_pdf", "MSc Thesis Proposal", "documents/ThesisProposal.pdf", "PDF", "ThesisProposal.pdf"),
            ("paper_pdf", "Thesis Abstract Brief", "documents/ThesisParagraph.pdf", "PDF", "ThesisParagraph.pdf"),
            ("github_repo", "Genesis Visual Programming Repo", "https://github.com/iebeid/genesis-visual-programming.git", "GitHub", None),
            ("screenshot", "Genesis IDE UI", "images/thesis1.png", "PNG", None),
            ("screenshot", "GDE Algorithm Animation", "images/thesis2.jpg", "JPG", None),
            ("screenshot", "Genesis Visual Code Generation", "images/thesis3.jpg", "JPG", None),
        ],
    },
    {
        "slug": "icas-vii",
        "title": "Intersection Collision Avoidance System (ICAS / VII)",
        "tagline": "Distinctive BSc Capstone: Vehicle-to-Infrastructure Automated Traffic Safety",
        "short_summary": "Distinctive Bachelor's Capstone Project (Ain Shams University, 2008) designing an automated Vehicle-Infrastructure Integration (VII) system for real-time intersection collision avoidance.",
        "full_description": "Recognized with Distinction at Ain Shams University Faculty of Engineering; integrates wireless vehicular telemetry, embedded hardware sensors, and real-time intersection kinematic collision prediction.",
        "category": "Legacy & Foundational Systems",
        "domain_stage": "foundational",
        "status": "BSc Capstone (Distinction)",
        "year_start": 2007,
        "year_end": 2008,
        "institution_or_org": "Ain Shams University",
        "grant_award": "Distinctive Capstone Project Award (2008)",
        "tech_stack": ["Embedded Systems", "C / C++", "V2I Communications", "Real-Time Control"],
        "code_snippet": None,
        "license_model": "Academic Capstone",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 22,
        "tags": ["Embedded Systems", "V2I", "Autonomous Safety", "BSc Capstone", "Award"],
        "artifacts": [
            ("paper_pdf", "VII / ICAS Final Thesis", "documents/The-VII-propject-V3.pdf", "PDF", "The-VII-propject-V3.pdf"),
            ("slides", "Capstone Defense Presentation", "documents/Graduation_Project_Presentation.pdf", "PDF", "Graduation_Project_Presentation.pdf"),
            ("screenshot", "ICAS Architecture", "images/icas.png", "PNG", None),
            ("screenshot", "V2I GPS Telemetry Interface", "images/icas2.png", "PNG", None),
            ("screenshot", "Trajectory Detection Map", "images/icas3.png", "PNG", None),
        ],
    },
    {
        "slug": "atu-cis-web",
        "title": "Academic Department Web Architecture & Student Affairs",
        "tagline": "University Portal Engineering, ABET Tracking & International Student Systems",
        "short_summary": "Comprehensive architecture specifications for university departmental portals, ABET accreditation tracking, and international student service operations developed at Arkansas Tech University.",
        "full_description": "Engineered department information portals (INFT5303), curriculum guides for the English Language Institute, and international student exchange operational systems at Arkansas Tech University.",
        "category": "Legacy & Foundational Systems",
        "domain_stage": "foundational",
        "status": "Academic Systems",
        "year_start": 2011,
        "year_end": 2013,
        "institution_or_org": "Arkansas Tech University",
        "grant_award": None,
        "tech_stack": ["Web Architecture", "HTML / CSS", "Information Systems", "ABET"],
        "code_snippet": None,
        "license_model": "Academic",
        "price_display": None,
        "storefront_category": None,
        "is_featured": 0,
        "is_storefront": 0,
        "display_order": 23,
        "tags": ["Web Architecture", "Arkansas Tech", "Student Affairs", "ABET"],
        "artifacts": [
            ("design_doc", "Department Portal Specification", "documents/department_website.pdf", "PDF", "department_website.pdf"),
            ("paper_pdf", "ATU CIS Department Outline", "documents/Arkansas Tech University.pdf", "PDF", "Arkansas Tech University.pdf"),
            ("paper_pdf", "Institutional Profile", "documents/Arkansas_Tech_University_Profile.pdf", "PDF", "Arkansas_Tech_University_Profile.pdf"),
            ("paper_pdf", "International Services Guide", "documents/RFsingaporefinal_compact_2_edited.pdf", "PDF", "RFsingaporefinal_compact_2_edited.pdf"),
            ("paper_pdf", "ELI Curriculum Architecture", "documents/English Language Institute.pdf", "PDF", "English Language Institute.pdf"),
            ("screenshot", "IMSSO Portal Architecture", "images/imsso1.png", "PNG", None),
            ("screenshot", "Student Affairs Dashboard", "images/imsso2.png", "PNG", None),
        ],
    },
]


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    ensure_schema(cur)
    doc_map = get_doc_id_map(cur)

    # Clear existing normalized project tables cleanly so re-runs are idempotent
    cur.execute("DELETE FROM project_courses")
    cur.execute("DELETE FROM project_tags")
    cur.execute("DELETE FROM project_publications")
    cur.execute("DELETE FROM project_artifacts")
    cur.execute("DELETE FROM projects")

    # Fetch publications index
    cur.execute("SELECT id, title, doi FROM publications")
    pubs = cur.fetchall()

    for p in PROJECTS:
        cur.execute("""
            INSERT INTO projects (
                slug, title, tagline, short_summary, full_description,
                category, domain_stage, status, year_start, year_end,
                institution_or_org, grant_award, tech_stack, code_snippet,
                license_model, price_display, storefront_category,
                is_featured, is_storefront, is_public, display_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            p["slug"],
            p["title"],
            p["tagline"],
            p["short_summary"],
            p["full_description"],
            p["category"],
            p["domain_stage"],
            p["status"],
            p["year_start"],
            p["year_end"],
            p["institution_or_org"],
            p["grant_award"],
            json.dumps(p["tech_stack"]),
            p["code_snippet"],
            p["license_model"],
            p["price_display"],
            p["storefront_category"],
            p["is_featured"],
            p["is_storefront"],
            p["display_order"],
        ))
        project_id = cur.lastrowid

        # Insert artifacts
        for order_idx, (a_type, label, url_path, badge, doc_filename) in enumerate(p.get("artifacts", []), 1):
            doc_id = doc_map.get(doc_filename) if doc_filename else None
            cur.execute("""
                INSERT OR IGNORE INTO project_artifacts (
                    project_id, artifact_type, label, url_or_rel_path, format_badge, document_id, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (project_id, a_type, label, url_path, badge, doc_id, order_idx))

        # Insert tags
        for tag in p.get("tags", []):
            cur.execute("INSERT OR IGNORE INTO project_tags (project_id, tag) VALUES (?, ?)", (project_id, tag))

        # Link publications by DOI or title prefix
        for doi in p.get("pub_dois", []):
            for pub_id, pub_title, pub_doi in pubs:
                if pub_doi and doi.lower() in pub_doi.lower():
                    cur.execute("INSERT OR IGNORE INTO project_publications (project_id, publication_id) VALUES (?, ?)", (project_id, pub_id))
        for tmatch in p.get("pub_title_matches", []):
            for pub_id, pub_title, pub_doi in pubs:
                if pub_title and tmatch.lower() in pub_title.lower():
                    cur.execute("INSERT OR IGNORE INTO project_publications (project_id, publication_id) VALUES (?, ?)", (project_id, pub_id))

    conn.commit()

    # Summary audit printout
    cur.execute("SELECT COUNT(*) FROM projects")
    n_proj = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM project_artifacts")
    n_art = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM project_publications")
    n_pub = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM project_tags")
    n_tag = cur.fetchone()[0]

    print("=" * 72)
    print(f"PHASE 1 COMPLETE: Normalized Project Backbone Populated in {DB_PATH.name}")
    print("=" * 72)
    print(f"  projects             : {n_proj} canonical projects")
    print(f"  project_artifacts    : {n_art} linked codebases / demos / datasets / PDFs / videos")
    print(f"  project_publications : {n_pub} publication links")
    print(f"  project_tags         : {n_tag} normalized tags")
    print("\nProject Inventory:")
    cur.execute("""
        SELECT p.display_order, p.slug, p.category, p.is_featured, p.is_storefront,
               (SELECT COUNT(*) FROM project_artifacts a WHERE a.project_id = p.id) AS art_cnt
        FROM projects p ORDER BY p.display_order
    """)
    for order, slug, cat, feat, sf, acnt in cur.fetchall():
        flags = []
        if feat: flags.append("FEATURED")
        if sf: flags.append("STOREFRONT")
        print(f"  {order:2d}. {slug:<30} | {cat:<36} | artifacts={acnt:2d} | {','.join(flags)}")

    conn.close()


if __name__ == "__main__":
    main()
