import sqlite3

conn = sqlite3.connect('data/content.db')
cur = conn.cursor()

cur.execute("SELECT content_html, content_text FROM page_sections WHERE page_slug='scholarship' AND section_key='poetry'")
row = cur.fetchone()
content_html, content_text = row

# Find the quote block to replace or enhance
old_block_marker = "<!-- Personal Epigraph / Closing Aphorism -->"
idx = content_html.find(old_block_marker)
assert idx != -1, "Old quote block marker not found"

end_idx = content_html.find("</section>", idx)
assert end_idx != -1, "</section> not found"

new_dual_quotes_html = '''<!-- Personal Epigraphs / Closing Aphorisms -->
<div class="mt-12 pt-8 border-t border-emerald-100 space-y-6">
    <!-- Quote 1: Purpose & Impact -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-emerald-900 via-emerald-800 to-teal-900 text-white p-8 sm:p-10 shadow-lg border border-emerald-700/50">
        <!-- Subtle decorative water ripple background effect -->
        <div class="absolute -right-12 -bottom-12 w-64 h-64 rounded-full border border-emerald-500/20 pointer-events-none"></div>
        <div class="absolute -right-20 -bottom-20 w-80 h-80 rounded-full border border-emerald-400/10 pointer-events-none"></div>
        <div class="absolute top-4 left-6 text-emerald-400/20 text-6xl font-serif select-none pointer-events-none leading-none">
            <i class="fas fa-quote-left"></i>
        </div>

        <div class="relative z-10 max-w-2xl mx-auto text-center">
            <p class="font-serif italic text-lg sm:text-xl md:text-2xl text-emerald-50 leading-relaxed font-light tracking-wide mb-4">
                &ldquo;In constant search for a stone for when I cast it in the pond of life it creates a significant ripple.&rdquo;
            </p>
            <div class="flex items-center justify-center gap-3">
                <span class="h-px w-8 bg-emerald-400/40"></span>
                <span class="text-xs sm:text-sm font-semibold uppercase tracking-widest text-emerald-300 font-sans">
                    Dr. Islam Akef Ebeid
                </span>
                <span class="h-px w-8 bg-emerald-400/40"></span>
            </div>
            <p class="text-[11px] text-emerald-300/70 mt-1 font-mono uppercase tracking-wider">
                Personal Reflection &bull; Philosophy of Impact
            </p>
        </div>
    </div>

    <!-- Quote 2: Adversity, Healing & Transformation -->
    <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-teal-950 to-emerald-950 text-white p-8 sm:p-10 shadow-lg border border-teal-800/40">
        <!-- Subtle decorative glow rings -->
        <div class="absolute -left-12 -bottom-12 w-64 h-64 rounded-full border border-teal-500/15 pointer-events-none"></div>
        <div class="absolute -left-20 -bottom-20 w-80 h-80 rounded-full border border-emerald-400/10 pointer-events-none"></div>
        <div class="absolute top-4 right-6 text-teal-400/20 text-6xl font-serif select-none pointer-events-none leading-none">
            <i class="fas fa-quote-right"></i>
        </div>

        <div class="relative z-10 max-w-3xl mx-auto text-center">
            <p class="font-serif italic text-base sm:text-lg md:text-xl text-teal-50/95 leading-relaxed font-light tracking-wide mb-4">
                &ldquo;The hardest part about adversity comes after healing. It&rsquo;s the belief that since there was an adverse event it must have had a negative impact on us or have broken us in ways that we can&rsquo;t fully overcome nor understand. Yet that might not be the case. At that point transformation happens.&rdquo;
            </p>
            <div class="flex items-center justify-center gap-3">
                <span class="h-px w-8 bg-teal-400/40"></span>
                <span class="text-xs sm:text-sm font-semibold uppercase tracking-widest text-teal-300 font-sans">
                    Dr. Islam Akef Ebeid
                </span>
                <span class="h-px w-8 bg-teal-400/40"></span>
            </div>
            <p class="text-[11px] text-teal-300/70 mt-1 font-mono uppercase tracking-wider">
                Personal Reflection &bull; On Resilience, Healing &amp; Transformation
            </p>
        </div>
    </div>
</div>
'''

new_content_html = content_html[:idx] + new_dual_quotes_html + "\n" + content_html[end_idx:]

new_content_text = (content_text or "") + "\n\nThe hardest part about adversity comes after healing. It's the belief that since there was an adverse event it must have had a negative impact on us or have broken us in ways that we can't fully overcome nor understand. Yet that might not be the case. At that point transformation happens. - Dr. Islam Akef Ebeid"

cur.execute("UPDATE page_sections SET content_html=?, content_text=? WHERE page_slug='scholarship' AND section_key='poetry'", (new_content_html, new_content_text))
conn.commit()
conn.close()
print("[OK] Successfully updated scholarship quotes with adversity and transformation quote")
