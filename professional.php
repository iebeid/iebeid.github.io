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
            <div style="float: left; width: 500px; height:150px; margin: 0px; padding: 0px;"> 
                <p>Islam Akef Ebeid</p> 
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
                        <div class="divTableCell"><fieldset style="border: 0;"><legend><b>Companies I worked for</b></legend>
                                <p>
                                    <a href="http://www.intel.com/content/www/us/en/homepage.html" target="_blank">Intel</a><br/>
                                    <a href="https://inaboard.ark.org/" target="_blank">Information Network of Arkansas</a><br/>
                                    <a href="http://www.wedotechnologies.com/en/" target="_blank">Wedo Technologies</a><br/>
                                    <a href="https://www.orange.com/en/home" target="_blank">Orange Telecom</a><br/>
                                    <a href="http://www.xpressintegration.com/" target="_blank">Xpress Integration</a><br/>
                                    <a href="http://www.iam.ma/index.aspx" target="_blank">Maroc Telecom</a><br/>
                                    <a href="https://www.tunisietelecom.tn/Fr" target="_blank">Tunisie Telecom</a><br/>
                                    <a href="http://hannainst.com/" target="_blank">Hanna Instruments</a><br/>
                                    <a href="http://gizasystems.com/" target="_blank">Giza Systems</a><br/>
                                    <a href="https://www.vodafone.com/content/index.html" target="_blank">Vodafone</a><br/>
                                </p>
                            </fieldset>
                        </div>
                        <div class="divTableCell"><fieldset style="border: 0;"><legend><b>Job Search Tools I recommend</b></legend>
                                <p>
                                    <a href="https://www.monster.com/account/homepage/" target="_blank">Monster</a><br/>
                                    <a href="https://www.glassdoor.com/index.htm" target="_blank">Glassdoor</a><br/>
                                    <a href="https://www.indeed.com/" target="_blank">Indeed</a><br/>
                                    <a href="https://www.freelancer.com/" target="_blank">Freelancer</a><br/>
                                    <a href="http://www.tutor.com/" target="_blank">Tutor</a><br/> 
                                </p>
                            </fieldset>
                        </div>
                    </div>
                </div>
            </div>  
            <br/>
            <hr/>
            <div id="content" class="module"><h1>Information Network of Arkansas</h1>
                <?php
                $username = "ebeid";
                $password = "ebeid";
                $database = "ebeid";
                $mysqli = new mysqli("localhost", $username, $password, $database);
                if ($mysqli->connect_errno) {
                    printf("Connect failed: %s\n", $mysqli->connect_error);
                    exit();
                }
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Professional' and organizations_id = 3")) {
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
            <div id="content" class="module"><h1>Xpress Integration</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Professional' and organizations_id = 6")) {
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
            <div id="content" class="module"><h1>Orange Telecom</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Professional' and organizations_id = 5")) {
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
            <div id="content" class="module"><h1>Wedo Technologies</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Professional' and organizations_id = 4")) {
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
            <div id="content" class="module"><h1>Vodafone</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Professional' and organizations_id = 8")) {
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
            <div id="content" class="module"><h1>Freelance</h1>
                <?php
                if ($result = $mysqli->query("SELECT * FROM projects where type = 'Professional' and organizations_id = 1")) {
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
                $mysqli->close();
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