import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\research\research.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I will add TransER and MedGCN to the "Data Quality, Engineering & Natural Language Processing" section.
# First, let's find that section. It contains: <!-- ModER Entity Resolution -->

new_cards = r'''
                    <!-- TransER -->
                    <div class="bg-white p-6 rounded-lg shadow-md border-t-4 border-indigo-600 flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between mb-2">
                                <h3 class="text-xl font-bold text-gray-900">TransER: Unsupervised Entity Resolution</h3>
                                <span class="tag">KDD Draft</span>
                            </div>
                            <p class="text-sm font-semibold text-indigo-700 mb-3">Transformational Embeddings for Data Quality</p>
                            <p class="text-sm text-gray-600 leading-relaxed mb-4">
                                TransER introduces an unsupervised entity resolution approach via transformational embeddings, mitigating the quadratic complexity of traditional pairwise comparisons. It leverages graph neural network concepts and transformational embeddings analogous to TransE to automate data cleaning, curation, and integration without handcrafting syntactic rules.
                            </p>
                        </div>
                        <div class="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2 text-xs">
                            <span class="bg-gray-100 text-gray-600 px-2 py-1 rounded">Entity Resolution</span>
                            <span class="bg-gray-100 text-gray-600 px-2 py-1 rounded">Unsupervised Learning</span>
                            <span class="bg-gray-100 text-gray-600 px-2 py-1 rounded">Data Curation</span>
                        </div>
                    </div>

                    <!-- MedGCN -->
                    <div class="bg-white p-6 rounded-lg shadow-md border-t-4 border-indigo-600 flex flex-col justify-between">
                        <div>
                            <div class="flex items-center justify-between mb-2">
                                <h3 class="text-xl font-bold text-gray-900">MedGCN: Biomedical NER</h3>
                                <span class="tag">MCBIOS 2024</span>
                            </div>
                            <p class="text-sm font-semibold text-indigo-700 mb-3">Query-time Character Level Embedding via Bidirectional GCNs</p>
                            <p class="text-sm text-gray-600 leading-relaxed mb-4">
                                A novel approach to Biomedical Named Entity Recognition (NER) that recasts the problem as a character-level representation of tokens in a directed graph. Trained via a Bidirectional Graph Convolutional Neural Network, MedGCN operates on the fly without the overhead or carbon footprint of fine-tuning large language models.
                            </p>
                        </div>
                        <div class="mt-4 pt-4 border-t border-gray-100 flex flex-wrap gap-2 text-xs">
                            <span class="bg-gray-100 text-gray-600 px-2 py-1 rounded">Biomedical NER</span>
                            <span class="bg-gray-100 text-gray-600 px-2 py-1 rounded">Graph Convolutional Networks</span>
                            <span class="bg-gray-100 text-gray-600 px-2 py-1 rounded">NLP</span>
                        </div>
                    </div>
'''

# Looking for <!-- ModER Entity Resolution -->
target = r'(<!-- ModER Entity Resolution -->)'
if 'TransER' not in content:
    match = re.search(target, content)
    if match:
        content = content[:match.start()] + new_cards + "\n                    " + content[match.start():]
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated research.html")
    else:
        print("Could not find the target section")
else:
    print("Already updated")

