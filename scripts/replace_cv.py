import io
import re

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\home\home.html'

with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_unt = '<p><span class="font-semibold text-gray-800">2022 – 2023:</span> Postdoctoral Research Associate at the <strong>University of North Texas (UNT)</strong> conducting NIH-funded Graph Neural Network research for drug repurposing; peer reviewer for <em>Cambridge University Press Journal of Natural Language Engineering</em> and <em>IEEE BIBM</em>.</p>'
new_unt = '<p><span class="font-semibold text-gray-800">2022 – 2023:</span> Postdoctoral Research Associate at the <strong>University of North Texas (UNT)</strong> conducting NIH-funded Graph Neural Network research for drug repurposing with Dr. Serdar Bozdag, developing novel algorithms for identifying drug candidates for complex diseases, and contributing to NIH R01 grant proposals focused on graph representation learning; peer reviewer for <em>Cambridge University Press Journal of Natural Language Engineering</em> and <em>IEEE BIBM</em>.</p>'

content = content.replace(old_unt, new_unt)

old_ut = '<p><span class="font-semibold text-gray-800">2017 – 2020:</span> Doctoral Researcher & Teaching Fellow at <strong>The University of Texas at Austin</strong> and the <strong>Texas Advanced Computing Center (TACC)</strong> (funded by <strong>Lockheed Martin</strong> and <strong>Intel</strong>); won the <strong>Best Short Paper Award at ACM SIGCHI ETRA 2019</strong>, <strong>UT Austin Professional Development Award (2019)</strong>, and <strong>UT Austin Graduate Recruitment Fellowship (2017)</strong>; served as Editorial Fellow at the <em>Journal of Information & Culture</em> (UT Press).</p>'
new_ut = '<p><span class="font-semibold text-gray-800">2017 – 2020:</span> Doctoral Researcher & Teaching Fellow at <strong>The University of Texas at Austin</strong> and the <strong>Texas Advanced Computing Center (TACC)</strong> (funded by <strong>Lockheed Martin</strong> and <strong>Intel</strong>), focused on developing algorithms for assessing cognitive load via eye tracking in high situational awareness environments; won the <strong>Best Short Paper Award at ACM SIGCHI ETRA 2019</strong>, <strong>UT Austin Professional Development Award (2019)</strong>, and <strong>UT Austin Graduate Recruitment Fellowship (2017)</strong>; served as Editorial Fellow at the <em>Journal of Information & Culture</em> (UT Press).</p>'

content = content.replace(old_ut, new_ut)

old_vodafone = '<p><span class="font-semibold text-gray-800">Jul 2005 – Sep 2005:</span> <strong>Web Developer Intern</strong> at <strong>Vodafone Egypt</strong>, designing an internal C# timesheet web application.</p>'
new_vodafone = '<p><span class="font-semibold text-gray-800">2007 – 2008:</span> <strong>Software Engineering Intern</strong> at <strong>Giza Systems</strong> in Cairo, Egypt.</p>\n                                            <p><span class="font-semibold text-gray-800">Jul 2005 – Sep 2005:</span> <strong>Web Developer Intern</strong> at <strong>Vodafone Egypt</strong>, designing an internal C# timesheet web application.</p>'

content = content.replace(old_vodafone, new_vodafone)

with io.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Replaced successfully!")
