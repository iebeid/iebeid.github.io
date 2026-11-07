import re

html_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\hobbies\hobbies.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# We want to replace the standard "Travel" block with a more enriched one detailing 2025 trips.
travel_pattern = re.compile(r'<!-- Travel -->.*?</div>\s*</div>\s*</div>', re.DOTALL)
travel_replacement = r'''<!-- Travel -->
                <div class="bg-white p-6 rounded-lg shadow-md flex flex-col justify-between md:col-span-2 lg:col-span-3">
                    <div>
                        <div class="w-12 h-12 bg-teal-100 text-teal-600 rounded-full flex items-center justify-center text-xl mb-4">
                            <i class="fas fa-globe-americas"></i>
                        </div>
                        <h3 class="text-lg font-bold text-gray-900 mb-2">Travel &amp; Exploration (2025 Itinerary)</h3>
                        <p class="text-sm text-gray-600 leading-relaxed mb-4">
                            Exploring historical cities, diverse cultures, architectural landmarks, and natural wonders. Recent and upcoming travel highlights for 2025 include:
                        </p>
                        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
                            <div class="bg-teal-50 p-4 rounded-lg border border-teal-100">
                                <h4 class="font-bold text-teal-900 mb-1"><i class="fas fa-city mr-1"></i> Cairo, Egypt</h4>
                                <p class="text-xs text-teal-800">Visiting historic landmarks, cultural centers, and reconnecting with vibrant heritage.</p>
                            </div>
                            <div class="bg-teal-50 p-4 rounded-lg border border-teal-100">
                                <h4 class="font-bold text-teal-900 mb-1"><i class="fas fa-umbrella-beach mr-1"></i> Galveston, TX</h4>
                                <p class="text-xs text-teal-800">Beach camping and enjoying the coastal environment along the Gulf of Mexico.</p>
                            </div>
                            <div class="bg-teal-50 p-4 rounded-lg border border-teal-100">
                                <h4 class="font-bold text-teal-900 mb-1"><i class="fas fa-star-and-crescent mr-1"></i> Austin, TX (July 4)</h4>
                                <p class="text-xs text-teal-800">Participating in Muslim and Arab gathering events, community research, and cultural celebrations.</p>
                            </div>
                        </div>
                    </div>
                    <div class="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500">
                        Global &amp; Historical Exploration
                    </div>
                </div>'''

if '2025 Itinerary' not in content:
    content = travel_pattern.sub(travel_replacement, content)
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated hobbies.html")
else:
    print("Already updated hobbies.html")
