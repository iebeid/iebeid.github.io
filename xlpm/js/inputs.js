/* 
 Author : Islam Akef Ebeid
 Affiliations : University of Arkansas at Little Rock - Emerging Analytics Center
 */


var fastaText = "";
var dataText = "";
var firstPDB = "";
var secondPDB = "";
localFlag = false;

//$(window).resize(function (){
//main(fastaText, dataText);
//});


var vis = $("#draw"),
    aspect = vis.width() / vis.height(),
    container = vis.parent();


$(window).on("resize", function() {
    if(svgDrawnFlag==1){
        var targetWidth = container.width();
        vis.attr("width", targetWidth);
        vis.attr("height", Math.round(targetWidth / aspect));
        //main(fastaText, dataText);
        //clearSVG();
        //main(fastaText, dataText);
        d3.select("svg").remove();
    }
}).trigger("resize");
    
    
$(document).ready(function () {

   
    
    $("#fasta").hide();
    $("#data").hide();
    $("#choose").hide();
    $("#serverDiv").hide();
    $("#localDiv").hide();
    
    $("#viewViz").show();
     $("#mainButton").disabled = true;
     $("#clearButton").disabled = true;
     $("#secLevelButton").disabled = true;
     
    $("#vis").hide();
    $("#structure").hide();
    
    $("#fasta").show();
    

    
    var fastafileInput = document.getElementById('fastafile');
    fastafileInput.addEventListener('change', function (e) {
        var file = fastafileInput.files[0];
        var textType = /fasta.*/;
        if (file.name.match(textType)) {
            var reader = new FileReader();
            reader.onload = function (e) {
                fastaText = reader.result;
            };
            reader.readAsText(file);
            $("#fasta").hide();
            $("#data").show();
        } else {
            alert("File not supported!");
        }
    });
    var datafileInput = document.getElementById('datafile');
    datafileInput.addEventListener('change', function (e) {
        var file = datafileInput.files[0];
        var textType = /txt.*/;
        if (file.name.match(textType)) {
            var reader = new FileReader();
            reader.onload = function (e) {
                dataText = reader.result;
            };
            reader.readAsText(file);
            $("#data").hide();
            $("#choose").show();
        } else {
            alert("File not supported!");
        }
    });

    $("input[type='radio']").click(function () {
        if ($(this).attr("id") == "local") {
            $("#localDiv").show();
            $("#serverDiv").hide();
            $("#choose").hide();
            //$("#viewViz").show();
            localFlag = true;
        }

        if ($(this).attr("id") == "server") {
            $("#serverDiv").show();
            $("#localDiv").hide();
            $("#choose").hide();
            //$("#viewViz").show();
            localFlag = false;
        }
        
        if($(this).attr("id") == "nod"){
            $("#choose").hide();
        }
    });

    var firstPdbInput = document.getElementById('viewMol1');
    firstPdbInput.addEventListener('change', function (e) {
        var file = firstPdbInput.files[0];
        var textType = /pdb.*/;
        if (file.name.match(textType)) {
            var reader = new FileReader();
            reader.onload = function (e) {
                firstPDB = reader.result;
            };
            reader.readAsText(file);
        } else {
            alert("File not supported!");
        }
    });

    var secondPdbInput = document.getElementById('viewMol2');
    secondPdbInput.addEventListener('change', function (e) {
        var file = secondPdbInput.files[0];
        var textType = /pdb.*/;
        if (file.name.match(textType)) {
            var reader = new FileReader();
            reader.onload = function (e) {
                secondPDB = reader.result;
            };
            reader.readAsText(file);
            //$("#viewViz").show();
                //$("#serverDiv").hide();
    //$("#localDiv").hide();
        } else {
            alert("File not supported!");
        }
    });
   
    var pdbCode = document.getElementById('firstseq');
    var pdbCodeTwo = document.getElementById('secondseq');
    pdbCode.addEventListener('change', function (e) {     
     $("#mainButton").disabled = false;
     $("#clearButton").disabled = false;
     $("#secLevelButton").disabled = false;});
    pdbCodeTwo.addEventListener('change', function (e) {     
     $("#mainButton").disabled = false;
     $("#clearButton").disabled = false;
     $("#secLevelButton").disabled = false;});
    
//$("#viewViz").show();

});


function viewPDB(peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor){
        var glviewer = $3Dmol.createViewer("glmol01", {
        defaultcolors: $3Dmol.rasmolElementColors
    });
    glviewer.setBackgroundColor(0xffffff);
        var appleString = "";
    var pearString = "";
                appleString = firstPDB;
            var m = glviewer.addModel(appleString, "pdb", {doAssembly: true, duplicateAssemblyAtoms: true});
            m.setStyle({hetflag: false}, {cartoon: {}});
            var atomsList = m.getAtoms();
            var colorObj = new $3Dmol.Color();
            colorObj.setHex(selectedColor);
            var initColorObj = new $3Dmol.Color();
            initColorObj.setHex(initialColor);
            var previousColorObj = new $3Dmol.Color();
            previousColorObj.setHex(previousColor);
            var seqArray = peptide1;
            var anotherSeqArray = previousArray1;
            for (var i in atomsList) {
                var atomObject = atomsList[i];
                atomObject.color = initColorObj.getHex();
                if (previousArray1.indexOf(atomObject.resi) !== -1){
                    atomObject.color = previousColorObj.getHex();
                }
                if (seqArray.indexOf(atomObject.resi) !== -1) {
                    atomObject.color = colorObj.getHex();
                }
            }
            glviewer.zoomTo();
            glviewer.render();
            
                        pearString = secondPDB;
            var n = glviewer.addModel(pearString, "pdb", {doAssembly: true, duplicateAssemblyAtoms: true});
            n.setStyle({hetflag: false}, {cartoon: {}});
            var listofatoms = n.getAtoms();
            var colorObj = new $3Dmol.Color();
            colorObj.setHex(selectedColor);
            var initColorObj = new $3Dmol.Color();
            initColorObj.setHex(initialColor);
            var previousColorObj = new $3Dmol.Color();
            previousColorObj.setHex(previousColor);
            var seqArray = peptide2;
            var anotherSeqArray = previousArray2;
            for (var i in listofatoms) {
                var atomObject = listofatoms[i];
                atomObject.color = initColorObj.getHex();
                if(previousArray2.indexOf(atomObject.resi) !== -1){
                    atomObject.color = previousColorObj.getHex();
                }
                if (seqArray.indexOf(atomObject.resi) !== -1) {
                    atomObject.color = colorObj.getHex();
                }
            }
            glviewer.zoomTo();
            glviewer.render();
}
function constructStructuresPDB(){
    var peptideArray1 = [0];
    var peptideArray2 = [0];
    var previousArray1 = [0];
    var previousArray2 = [0];
    viewPDB(peptideArray1, peptideArray2, previousArray1, previousArray2, "0xA9A9A9", "0xA9A9A9", "0xA9A9A9");
    
}



function constructStructures(){

    var peptideArray1 = [0];
    var peptideArray2 = [0];
    var previousArray1 = [0];
    var previousArray2 = [0];
    view($("#firstseq").val(), $("#secondseq").val(), peptideArray1, peptideArray2, previousArray1, previousArray2, "0xA9A9A9", "0xA9A9A9", "0xA9A9A9");
}

 
function view(pdbid_1, pdbid_2, peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor) {
   
   

        var glviewer = $3Dmol.createViewer("glmol01", {
        defaultcolors: $3Dmol.rasmolElementColors
    });

    glviewer.setBackgroundColor(0xffffff);
    
    var appleString = "";
    var pearString = "";
    appleUri = "http://www.rcsb.org/pdb/files/" + pdbid_1.toString().toUpperCase() + ".pdb";
    pearUri = "http://www.rcsb.org/pdb/files/" + pdbid_2.toString().toUpperCase() + ".pdb";

    $.ajax({
        url: appleUri,
        type: "get",
        success: function (ret) {
            appleString = ret;
            var m = glviewer.addModel(appleString, "pdb", {doAssembly: true, duplicateAssemblyAtoms: true});
            m.setStyle({hetflag: false}, {cartoon: {}});
            var atomsList = m.getAtoms();
            var colorObj = new $3Dmol.Color();
            colorObj.setHex(selectedColor);
            var initColorObj = new $3Dmol.Color();
            initColorObj.setHex(initialColor);
            var previousColorObj = new $3Dmol.Color();
            previousColorObj.setHex(previousColor);
            var seqArray = peptide1;
            var anotherSeqArray = previousArray1;
            for (var i in atomsList) {
                var atomObject = atomsList[i];
                atomObject.color = initColorObj.getHex();
                if (previousArray1.indexOf(atomObject.resi) !== -1){
                    atomObject.color = previousColorObj.getHex();
                }
                if (seqArray.indexOf(atomObject.resi) !== -1) {
                    atomObject.color = colorObj.getHex();
                }
            }
//                            glviewer.zoomTo();
//            glviewer.render();
            
        }
    });
    $.ajax({
        url: pearUri,
        type: "get",
        success: function (ret) {
            pearString = ret;
            var n = glviewer.addModel(pearString, "pdb", {doAssembly: true, duplicateAssemblyAtoms: true});
            n.setStyle({hetflag: false}, {cartoon: {}});
            var listofatoms = n.getAtoms();
            var colorObj = new $3Dmol.Color();
            colorObj.setHex(selectedColor);
            var initColorObj = new $3Dmol.Color();
            initColorObj.setHex(initialColor);
            var previousColorObj = new $3Dmol.Color();
            previousColorObj.setHex(previousColor);
            var seqArray = peptide2;
            var anotherSeqArray = previousArray2;
            for (var i in listofatoms) {
                var atomObject = listofatoms[i];
                atomObject.color = initColorObj.getHex();
                if(previousArray2.indexOf(atomObject.resi) !== -1){
                    atomObject.color = previousColorObj.getHex();
                }
                if (seqArray.indexOf(atomObject.resi) !== -1) {
                    atomObject.color = colorObj.getHex();
                }
            }
            glviewer.zoomTo();
            glviewer.render();
        }
    });

    console.log("---model");
    console.log(glviewer);
}

function updateView(){
        var model = glviewer.getModel();
        console.log("model");
        console.log(model);
        console.log(glviewer);
        
        glviewer.zoomTo();
        glviewer.render();
}