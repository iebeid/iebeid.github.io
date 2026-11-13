with open('js/portal.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Chrome drop
old_chrome_drop = """        const newBm = {
            id: newId,
            name: data.title,
            url: data.url,
            category: category,
            subfolder: subfolder,
            path: `${category} / ${subfolder}`,
            path_parts: [category, subfolder],
            domain: data.domain,
            ai_tags: aiTags,
            isCustom: true
        };"""

new_chrome_drop = """        const desc = generateBookmarkDescription(data.title, data.domain, subfolder, category, data.url);
        const newBm = {
            id: newId,
            name: data.title,
            url: data.url,
            category: category,
            subfolder: subfolder,
            path: `${category} / ${subfolder}`,
            path_parts: [category, subfolder],
            domain: data.domain,
            ai_tags: aiTags,
            description: desc,
            isCustom: true
        };"""

assert old_chrome_drop in code, "old_chrome_drop not found"
code = code.replace(old_chrome_drop, new_chrome_drop, 1)

# 2. Add / Edit modal
old_modal_add = """                const newBm = {
                    id: newId,
                    name: name,
                    url: url,
                    category: category,
                    subfolder: subfolder,
                    path: `${category} / ${subfolder}`,
                    path_parts: [category, subfolder],
                    domain: domain,
                    ai_tags: finalTags,
                    isCustom: true
                };"""

new_modal_add = """                const desc = generateBookmarkDescription(name, domain, subfolder, category, url);
                const newBm = {
                    id: newId,
                    name: name,
                    url: url,
                    category: category,
                    subfolder: subfolder,
                    path: `${category} / ${subfolder}`,
                    path_parts: [category, subfolder],
                    domain: domain,
                    ai_tags: finalTags,
                    description: desc,
                    isCustom: true
                };"""

assert old_modal_add in code, "old_modal_add not found"
code = code.replace(old_modal_add, new_modal_add, 1)

# 3. Edit existing
old_modal_edit = """                    custom[existingIdx].domain = domain;
                    custom[existingIdx].ai_tags = finalTags;
                    saveCustomBookmarks(custom);"""

new_modal_edit = """                    custom[existingIdx].domain = domain;
                    custom[existingIdx].ai_tags = finalTags;
                    custom[existingIdx].description = generateBookmarkDescription(name, domain, subfolder, category, url);
                    saveCustomBookmarks(custom);"""

assert old_modal_edit in code, "old_modal_edit not found"
code = code.replace(old_modal_edit, new_modal_edit, 1)

with open('js/portal.js', 'w', encoding='utf-8') as f:
    f.write(code)

print("[OK] Attached generateBookmarkDescription to Chrome drops and manual bookmark creations in js/portal.js")
