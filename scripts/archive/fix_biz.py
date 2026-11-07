import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\business\business.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# I will find the block I added and move it inside the bg-gradient div.
# the bg-gradient div closes at </div>\n                </div>\n            \n                    <!-- Unity Consultancy
# Wait, let's just grab the whole block and put it before the closing </div> of the main card.

pattern = re.compile(r'(\s*</div>\s*</div>\s*)\n\s*<!-- Unity Consultancy & Pharma Pitch Info -->.*?</div>\s*</div>\s*</div>', re.DOTALL)
match = pattern.search(content)

if match:
    # We want to swap the order. The matched text is:
    # </div> </div> \n <!-- Unity Consultancy... --> ... </div> </div> </div>
    # Actually, let's just extract the Unity Consultancy block, remove it, and insert it before the last </div> of the main card.

    # Find the unity block
    unity_block_pattern = re.compile(r'\s*<!-- Unity Consultancy & Pharma Pitch Info -->.*?</div>\s*</div>\s*</div>', re.DOTALL)
    unity_match = unity_block_pattern.search(content)
    if unity_match:
        unity_text = unity_match.group(0)
        content = content[:unity_match.start()] + content[unity_match.end():]
        
        # Now find where to insert it. We want it inside the first bg-gradient-to-r div.
        # Let's find: <a href="storefront.html#catalog" ... </a></div></div> and insert right after it.
        target_re = re.compile(r'(<a href="storefront.html#catalog".*?</a>\s*</div>\s*</div>)', re.DOTALL)
        t_match = target_re.search(content)
        if t_match:
            content = content[:t_match.end()] + unity_text + "\n" + content[t_match.end():]
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Fixed business.html layout")
        else:
            print("Could not find target to insert in business.html")
    else:
        print("Could not find unity block")
else:
    print("Pattern not matched entirely, let me try a different approach.")
