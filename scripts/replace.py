import io

file_path = r'G:\My Drive\Documents\Projects\Career\Website\iebeid.github.io\pages\home\home.html'

with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_2020 = '<p><span class="font-semibold text-gray-800">2020 – 2021:</span> Earned M.Sc. in Computer & Information Science; co-authored the landmark <strong>PubMed Knowledge Graph</strong> in <em>Nature Scientific Data</em> (2020), COVID-19 literature networks in <em>Scientometrics</em> (2021), and computational social science research in <em>Voluntas</em> (2021); completed Data Science Research Internship at <strong>AbbVie Inc.</strong> and selected for the <strong>Data Science for Social Good Fellowship</strong>.</p>'
new_2020 = '<p><span class="font-semibold text-gray-800">2020 – 2021:</span> Earned M.Sc. in Computer & Information Science; co-authored the landmark <strong>PubMed Knowledge Graph</strong> in <em>Nature Scientific Data</em> (2020), COVID-19 literature networks in <em>Scientometrics</em> (2021), and computational social science research in <em>Voluntas</em> (2021); completed Data Science Research Internship at <strong>AbbVie Inc.</strong> (Urbana-Champaign, IL) conducting research on data-driven drug discovery via graph representation learning, and selected for the <strong>Data Science for Social Good Fellowship</strong>.</p>'

content = content.replace(old_2020, new_2020)

old_2011 = '<p><span class="font-semibold text-gray-800">2011 – 2014:</span> Software Developer at <strong>Arkansas.gov (NIC Inc.)</strong> building state e-government portals; graduated with a <strong>Professional M.Sc. in Computer & Information Science</strong> from <strong>Arkansas Tech University</strong> (2013).</p>'
new_2011 = '<p><span class="font-semibold text-gray-800">2011 – 2014:</span> <strong>Software Developer</strong> at <strong>Arkansas.gov (NIC Inc.)</strong> building state e-government portals; served as a <strong>Graduate Assistant</strong> and earned a <strong>Professional M.Sc. in Information Technology</strong> from <strong>Arkansas Tech University</strong> (2013).</p>'

content = content.replace(old_2011, new_2011)

old_2005 = '<p><span class="font-semibold text-gray-800">2005 – 2011:</span> Telecom & Enterprise Software Engineer at <strong>WeDo Technologies</strong>, <strong>Orange Telecom (Mobinil)</strong>, and <strong>Xpress Integration</strong> (delivering Openwave SMSC/MMSC deployments for <em>Maroc Telecom</em> and <em>Tunisie Telecom</em>); Electronics Engineer at <strong>Hanna Instruments</strong>; earned <strong>B.Sc. in Electrical & Computer Engineering</strong> from <strong>Ain Shams University</strong> (2008, <em>Distinctive Capstone Project Award</em> for <em>ICAS</em>).</p>'

new_2005 = '''<p><span class="font-semibold text-gray-800">May 2011 – Aug 2011:</span> <strong>Software Delivery Consultant</strong> at <strong>WeDo Technologies</strong> (Cairo, Egypt), integrating RAID business and revenue assurance software.</p>
                                            <p><span class="font-semibold text-gray-800">Aug 2010 – May 2011:</span> <strong>Software Developer</strong> at <strong>Mobinil (France Telecom Egypt)</strong>, developing Java web services on the webMethods platform for CRM and Billing system integration.</p>
                                            <p><span class="font-semibold text-gray-800">Jan 2009 – Jul 2010:</span> <strong>Software Developer</strong> at <strong>Xpress Integration</strong>, delivering telecom billing management systems across Tunis (Tunisie Telecom), Rabat (Maroc Telecom), and Cairo (Ericsson).</p>
                                            <p><span class="font-semibold text-gray-800">Jul 2008 – Dec 2008:</span> <strong>Maintenance Engineer</strong> for chemical lab instruments at <strong>Hanna Instruments</strong> in Cairo.</p>
                                            <p><span class="font-semibold text-gray-800">Aug 2003 – Jul 2008:</span> Earned <strong>B.Sc. in Electrical & Computer Engineering</strong> from <strong>Ain Shams University</strong> with a <em>Distinctive Capstone Project Award</em> for an Intersection Collision Avoidance System (ICAS).</p>
                                            <p><span class="font-semibold text-gray-800">Jul 2005 – Sep 2005:</span> <strong>Web Developer Intern</strong> at <strong>Vodafone Egypt</strong>, designing an internal C# timesheet web application.</p>'''

content = content.replace(old_2005, new_2005)

with io.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Replaced successfully!")
