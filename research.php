<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>Islam Akef Ebeid</title>
        <link rel="shortcut icon" href="images/ebeid.ico" type="image/x-icon" />
        <style>@import url(css/style.css);</style>
    </head>
    <body>
        <header>
            <div style="float: left; width: 200px; height:150px; margin: 0px; padding: 0px;"> <img width="150px" height="150px" src="images/personal/islam.jpg"/> </div>
            <div style="float: left; width: 500px; height:150px; margin: 0px; padding: 0px;"> <p>Islam Akef Ebeid</p> 
                <div id="logo">
                    <script src="js/three.min.js"></script>
                    <script src="js/logo.js"></script>
                    <script>main();</script>
                </div>
            </div>
            <div style="float: left; width: 200px; height:200px; margin: 0px; padding: 0px; text-align: left;">
                <button type="button" title="My home page includes a small description of my self and main links to my online accounts" onclick="window.location.href = 'index.html';">Home</button><br/>
                <button type="button" title="The research page includes a list of my published projects and some experiments categorized by the institution that I completed that project at" onclick="window.location.href = 'research.html';">Research Projects</button><br/>
                <button type="button" title="A list of professional projects and role descriptions at every organization I worked for" onclick="window.location.href = 'professional.html';">Professional Projects</button><br/>
                <button type="button" title="A list of work samples" onclick="window.location.href = 'projects.html';">Selected Projects</button><br/>
                <button type="button" title="My personal blog; I post about Travel, Home Crafts and project progress" onclick="window.open('http://mindmitter.blogspot.com/');">Blog</button><br/>
                <button type="button" title="My personal resume/CV click to view in the browser pdf viewer and download" onclick="window.open('docs/resume.pdf');">Resume</button><br/>
            </div>
        </header>
        <section>
            <div class="divTable"><br/><br/><br/><br/>
                <div class="divTableBody">
                    <div class="divTableRow">
                        <div class="divTableCell"><fieldset style="border: 0;"><legend><b>Educational tools I use</b></legend>
                                <p>
                                    <a href="https://prezi.com/user/mmtnrbrwtz9t/" target="_blank">Prezi</a><br/>
                                    <a href="https://www.mendeley.com/profiles/islam-ebeid/" target="_blank">Mendeley</a><br/>
                                    <a href="https://www.khanacademy.org/profile/kaid_868273694547433415805526/" target="_blank">Khan Academy</a><br/>
                                    <a href="https://www.duolingo.com/IslamAkefE" target="_blank">Duolingo</a><br/>
                                    <a href="https://nvidia.qwiklab.com/dashboard" target="_blank">Qwiklab</a><br/>
                                    <a href="https://courses.edx.org/" target="_blank">Edx</a><br/>
                                    <a href="https://www.coursera.org/user/i/8b0d8962eafa196a205036ddfa7539b4" target="_blank">Coursera</a><br/>
                                </p>
                            </fieldset>
                        </div>
                        <div class="divTableCell"><fieldset style="border: 0;"><legend><b>Developer forums I contribute to</b></legend>
                                <p>
                                    <a href="http://stackoverflow.com/users/5012284/akef?tab=profile" target="_blank" title="Stackoverflow"><img width="50px" height="50px" src="images/social/1481094411_stackoverflow.png" alt="Stack Overflow"/></a>
                                    <a href="https://www.codeproject.com/" target="_blank" title="Code Project"><img width="50px" height="50px" src="images/social/codeproject.png" alt="Codeproject"/></a>
                                    <a href="https://software.intel.com/partner/app/dashboard?locale=en-us" target="_blank" title="Intel"><img width="50px" height="50px" src="images/social/intel.png" alt="Intel"/></a>
                                    <a href="https://developer.nvidia.com/" target="_blank" title="Nvidia"><img width="50px" height="50px" src="images/social/nvidia.png" alt="Nvidia"/></a>
                                    <a href="https://msdn.microsoft.com/en-us" target="_blank" title="Microsoft"><img width="50px" height="50px" src="images/social/vs.png" alt="Microsoft"/></a>
                                </p>
                            </fieldset>
                        </div>
                    </div>
                    <div class="divTableRow">
                        <div class="divTableCell"><fieldset style="border: 0;"><legend><b>Organizations I am a member at</b></legend>
                                <p>
                                    <a href="https://myacm.acm.org/dashboard.cfm?svc=curr" target="_blank">ACM</a><br/>
                                    <a href="http://www.ieee.org/index.html" target="_blank">IEEE</a><br/>
                                    <a href="https://www.computer.org/" target="_blank">IEEE - Computer Society</a><br/>
                                    <a href="http://www.imaging.org/site/ist/" target="_blank">Society of Imaging Science and Technologies</a><br/>
                                    <a href="https://nsf.gov/" target="_blank">National Science Foundation</a><br/>
                                </p>
                            </fieldset>
                        </div>
                        <div class="divTableCell"><fieldset style="border: 0;"><legend><b>Conferences and Journals I participated in</b></legend>
                                <p>
                                    <a href="http://www.imaging.org/site/IST/Conferences/EI_2017/IST/Conferences/EI_2017/Symposium_Overview.aspx" target="_blank">Electronic Imaging 2016</a><br/>
                                    <a href="https://mcbios.org/2015-mcbios-annual-conference" target="_blank">MCBIOS 2015 - MCBIOS 2016</a><br/>
                                    <a href="http://s2015.siggraph.org/" target="_blank">SIGGRAPH 2015</a><br/>
                                    <a href="https://www.imaging.org/site/IST/Publications/JIST/IST/Publications/Journal_of_Imaging_Science_and_Technology.aspx?hkey=7563ebfc-9a10-4e6e-8f31-268b49aec1a0" target="_blank">Journal of Imaging Science and Technologies</a><br/>
                                    <a href="http://sc16.supercomputing.org/" target="_blank">Super Computing 2016</a><br/>                                      
                                </p>
                            </fieldset>
                        </div>
                    </div>
                </div>
            </div>  
            <br/>
            <hr/>
            <div id="content" class="module"><h1>Highlights</h1>
                <?php
                $username = "ebeid";
                $password = "ebeid";
                $database = "ebeid";
                $mysqli = new mysqli("localhost", $username, $password, $database);
                if ($mysqli->connect_errno) {
                    printf("Connect failed: %s\n", $mysqli->connect_error);
                    exit();
                }
                if ($result = $mysqli->query("SELECT * FROM projects where id in (1,7,15,19,20,36,37,40) order by year desc")) {
                    if ($result) {
                        while ($row = mysqli_fetch_assoc($result)) {
                            echo "<fieldset style='border: 0;'>";
                            echo "<div style='width: 800px; height: 100px;'>";
                            echo "<div style='width: 100px; height: 100px; float: left;'><img width='100px' height='100px' src='" . $row['thumbnail'] . "'/></div>";
                            echo "<div style='width: 680px;  height: 20px; float: right;'><b>" . $row['title'] . "</b></div>";
                            echo "<div style='width: 680px;  height: 70px; float: right;'>" . $row['short_description'] . "</div>";
                            echo "<div style='width: 680px;  height: 10px; float: right;'>";
                            if ($row['url'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['url'] . "'>github</a>";
                            }
                            if ($row['video'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['video'] . "'>video</a>";
                            }
                            if ($row['paper'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['paper'] . "'>paper</a></div>";
                            }
                            echo "</div>";
                            echo "</fieldset>";
                        }
                    }
                    $result->close();
                    mysqli_more_results($mysqli);
                }
                ?>
            </div>
        </section>
        <section>
            <hr/>
            <div id="content" class="module"><h1>Intel</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Academic' and organizations_id = 2")) {
                    if ($result) {
                        while ($row = mysqli_fetch_assoc($result)) {
                            echo "<fieldset style='border: 0;'>";
                            echo "<div style='width: 800px; height: 100px;'>";
                            echo "<div style='width: 100px; height: 100px; float: left;'><img width='100px' height='100px' src='" . $row['thumbnail'] . "'/></div>";
                            echo "<div style='width: 680px;  height: 20px; float: right;'><b>" . $row['title'] . "</b></div>";
                            echo "<div style='width: 680px;  height: 70px; float: right;'>" . $row['short_description'] . "</div>";
                            echo "<div style='width: 680px;  height: 10px; float: right;'>";
                            if ($row['url'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['url'] . "'>github</a>";
                            }
                            if ($row['video'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['video'] . "'>video</a>";
                            }
                            if ($row['paper'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['paper'] . "'>paper</a></div>";
                            }
                            echo "</div>";
                            echo "</fieldset>";
                        }
                    }
                    $result->close();
                    mysqli_more_results($mysqli);
                }
                ?>
            </div>
        </section>
        <section>
            <hr/>
            <div id="content" class="module"><h1>University of Arkansas at Little Rock</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Academic' and organizations_id = 12")) {
                    if ($result) {
                        while ($row = mysqli_fetch_assoc($result)) {
                            echo "<fieldset style='border: 0;'>";
                            echo "<div style='width: 800px; height: 100px;'>";
                            echo "<div style='width: 100px; height: 100px; float: left;'><img width='100px' height='100px' src='" . $row['thumbnail'] . "'/></div>";
                            echo "<div style='width: 680px;  height: 20px; float: right;'><b>" . $row['title'] . "</b></div>";
                            echo "<div style='width: 680px;  height: 70px; float: right;'>" . $row['short_description'] . "</div>";
                            echo "<div style='width: 680px;  height: 10px; float: right;'>";
                            if ($row['url'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['url'] . "'>github</a>";
                            }
                            if ($row['video'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['video'] . "'>video</a>";
                            }
                            if ($row['paper'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['paper'] . "'>paper</a></div>";
                            }
                            echo "</div>";
                            echo "</fieldset>";
                        }
                    }
                    $result->close();
                    mysqli_more_results($mysqli);
                }
                ?>
            </div>
        </section>
        <section>
            <hr/>
            <div id="content" class="module"> <h1>Masters - Arkansas Tech University</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Academic' and organizations_id = 11")) {
                    if ($result) {
                        while ($row = mysqli_fetch_assoc($result)) {
                            echo "<fieldset style='border: 0;'>";
                            echo "<div style='width: 800px; height: 100px;'>";
                            echo "<div style='width: 100px; height: 100px; float: left;'><img width='100px' height='100px' src='" . $row['thumbnail'] . "'/></div>";
                            echo "<div style='width: 680px;  height: 20px; float: right;'><b>" . $row['title'] . "</b></div>";
                            echo "<div style='width: 680px;  height: 70px; float: right;'>" . $row['short_description'] . "</div>";
                            echo "<div style='width: 680px;  height: 10px; float: right;'>";
                            if ($row['url'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['url'] . "'>github</a>";
                            }
                            if ($row['video'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['video'] . "'>video</a>";
                            }
                            if ($row['paper'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['paper'] . "'>paper</a></div>";
                            }
                            echo "</div>";
                            echo "</fieldset>";
                        }
                    }
                    $result->close();
                    mysqli_more_results($mysqli);
                }
                ?>
            </div>
        </section>
        <section>
            <hr/>
            <div id="content" class="module"><h1>Undergraduate - Ain Shams University</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Academic' and organizations_id = 10")) {
                    if ($result) {
                        while ($row = mysqli_fetch_assoc($result)) {
                            echo "<fieldset style='border: 0;'>";
                            echo "<div style='width: 800px; height: 100px;'>";
                            echo "<div style='width: 100px; height: 100px; float: left;'><img width='100px' height='100px' src='" . $row['thumbnail'] . "'/></div>";
                            echo "<div style='width: 680px;  height: 20px; float: right;'><b>" . $row['title'] . "</b></div>";
                            echo "<div style='width: 680px;  height: 70px; float: right;'>" . $row['short_description'] . "</div>";
                            echo "<div style='width: 680px;  height: 10px; float: right;'>";
                            if ($row['url'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['url'] . "'>github</a>";
                            }
                            if ($row['video'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['video'] . "'>video</a>";
                            }
                            if ($row['paper'] != NULL) {
                                echo "  <a target='_blank' href='" . $row['paper'] . "'>paper</a></div>";
                            }
                            echo "</div>";
                            echo "</fieldset>";
                        }
                    }
                    $result->close();
                    mysqli_more_results($mysqli);
                }
                ?>
            </div>
        </section>
        <footer>
            <div id="logo"><br/><br/><br/><br/>
                <fieldset style="border: 0;">
                    <a href="https://www.facebook.com/i3akef" target="_blank" title="Facebook"><img width="30px" height="30px" src="images/social/1481140735_facebook.png"/></a>
                    <a href="https://twitter.com/i3akef" target="_blank" title="Twitter"><img width="30px" height="30px" src="images/social/1481140753_twitter.png"/></a>
                    <a href="https://plus.google.com/+IslamAkefEbeid" target="_blank" title="Google+"><img width="30px" height="30px" src="images/social/1481140811_google.png"/></a>
                    <a href="https://www.instagram.com/i3akef/" target="_blank" title="Instagram"><img width="30px" height="30px" src="images/social/1481140739_instagram.png"/></a>
                    <a href="https://www.quora.com/profile/Islam-Akef-Ebeid" target="_blank" title="Quora"><img width="30px" height="30px" src="images/social/1481153253_quora.png"/></a>
                    <a href="https://www.linkedin.com/in/i3akef" target="_blank" title="Linkedin"><img width="30px" height="30px" src="images/social/1481153224_linkedin_circle_black.png"/></a>
                    <a href="https://www.youtube.com/channel/UCI1m48CMEqYyD2MoLsHhDjw" target="_blank" title="Youtube"><img width="30px" height="30px" src="images/social/1481140818_youtube.png"/></a>
                    <a href="skype:islam.akef?userinfo" target="_blank" title="Skype"><img width="30px" height="30px" src="images/social/skype.png"/></a>
                    <a data-rel="external" href="tel:+14796921854" target ="_blank" title="WhatsApp Phone Number"><img width="30px" height="30px" src="images/social/whatsapp.png"/></a>
                </fieldset>
                <p>
                    Copyright © 2016 <a href="mailto:islam.akef@gmail.com" target ="_blank">Islam Akef Ebeid</a><br/>
                    <a href="http://miicard.me/c9KTg86F" target="_blank" title="Mii Card">Identity assured by miiCard : Click to Verify</a>
                </p>
            </div>
        </footer>
    </body>
</html>