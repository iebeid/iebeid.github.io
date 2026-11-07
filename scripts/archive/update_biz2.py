import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\business\business.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

new_content = r'''
                    <!-- Unity Consultancy & Pharma Pitch Info -->
                    <div class="mt-8 pt-8 border-t border-sky-800/60">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                            
                            <!-- Unity Consultancy Overview -->
                            <div>
                                <h3 class="text-xl font-bold text-white mb-3 flex items-center gap-2">
                                    <i class="fas fa-briefcase text-sky-400"></i> Unity Consultancy
                                </h3>
                                <p class="text-sm text-sky-100/90 mb-4">
                                    Our consultancy arm provides comprehensive services across the software lifecycle. We specialize in robust, scalable solutions and strategic project execution.
                                </p>
                                <ul class="space-y-2 text-sm text-sky-200">
                                    <li><i class="fas fa-check-circle text-emerald-400 mr-2"></i> <strong>Core Services:</strong> Data Storage, Data Analytics &amp; AI, Software Engineering, Full-Stack Solutions, Project Management.</li>
                                    <li><i class="fas fa-check-circle text-emerald-400 mr-2"></i> <strong>Key Projects:</strong> The Dallas Muslim News.</li>
                                    <li><i class="fas fa-check-circle text-emerald-400 mr-2"></i> <strong>Funding Strategy:</strong> Supported by Endowments and Zakat funding models.</li>
                                    <li><i class="fas fa-check-circle text-emerald-400 mr-2"></i> <strong>Team:</strong> Founded by Dr. Islam Akef Ebeid. Core Volunteers include Noor Atiyah.</li>
                                </ul>
                            </div>

                            <!-- Enterprise Pharma Pitch -->
                            <div>
                                <h3 class="text-xl font-bold text-white mb-3 flex items-center gap-2">
                                    <i class="fas fa-dna text-sky-400"></i> Pharma AI &amp; Network Biology Solutions
                                </h3>
                                <p class="text-sm text-sky-100/90 mb-4">
                                    Delivering enterprise-ready, secure AI systems for drug discovery. We build heterogeneous graph embeddings (PrimeKG, Hetionet) while rigorously addressing pharmaceutical intellectual property risks.
                                </p>
                                <ul class="space-y-2 text-sm text-sky-200">
                                    <li><i class="fas fa-shield-alt text-amber-400 mr-2"></i> <strong>Differential Privacy:</strong> DP-SGD and node-perturbation techniques neutralize membership inference attacks and protect proprietary targets.</li>
                                    <li><i class="fas fa-shield-alt text-amber-400 mr-2"></i> <strong>Graph Sanitization:</strong> Automated anomaly detection against graph poisoning in public databases (STRING, BioGRID).</li>
                                    <li><i class="fas fa-shield-alt text-amber-400 mr-2"></i> <strong>Confidential Computing:</strong> Secure inference enclaves (AMD SEV-SNP/Intel SGX) ensure zero-knowledge environments for sensitive repurposing models.</li>
                                </ul>
                            </div>

                        </div>
                    </div>
'''

if '<!-- Unity Consultancy Overview -->' not in content:
    # find the closing div of the main startup profile card which is rounded-2xl
    # We can just look for the first </section> inside the max-w-5xl div
    parts = content.split('</section>', 1)
    if len(parts) == 2:
        # Actually, let's insert it inside the rounded-2xl div. 
        # The rounded-2xl div contains the grid of 3 lifecycle pillars.
        # Let's insert it right after that grid and before the closing </div> of rounded-2xl.
        # To do this safely, let's look for:
        # <!-- 3 Lifecycle Pillars & Flagship Component Matrix Preview -->
        # then the </div> that closes the grid, then insert our new_content.
        
        target = r'(<a href="storefront.html#catalog" class="text-xs font-semibold text-sky-400 hover:text-sky-300 inline-flex items-center mt-auto">.*?</a>\s*</div>\s*</div>)'
        import re
        match = re.search(target, content, re.DOTALL)
        if match:
            content = content[:match.end()] + new_content + content[match.end():]
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Successfully updated HTML.")
        else:
            print("Target not found. Doing a fallback replacement.")
            content = parts[0] + new_content + "\n            </section>" + parts[1]
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Fallback successfully updated HTML.")
else:
    print("Already updated.")
