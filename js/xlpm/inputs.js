/* 
 * Author : Islam Akef Ebeid
 * Affiliations : University of Arkansas at Little Rock - Emerging Analytics Center
 * Enhanced for Unity Systems & Academic Portfolio Preset Demo
 */

var fastaText = "";
var dataText = "";
var firstPDB = "";
var secondPDB = "";
var localFlag = true;
var currentPresetId = "rim1_dimer";

function renderDual3DModels(pdbStr1, pdbStr2, peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor) {
    $("#glmol01").empty();
    var glviewer = $3Dmol.createViewer("glmol01", {
        defaultcolors: $3Dmol.rasmolElementColors
    });
    glviewer.setBackgroundColor(0xffffff);

    if (pdbStr1 && pdbStr1.length > 10) {
        var m = glviewer.addModel(pdbStr1, "pdb", {doAssembly: true, duplicateAssemblyAtoms: true});
        m.setStyle({hetflag: false}, {cartoon: {}});
        var atomsList = m.getAtoms();
        var colorObj = new $3Dmol.Color();
        colorObj.setHex(selectedColor);
        var initColorObj = new $3Dmol.Color();
        initColorObj.setHex(initialColor);
        var previousColorObj = new $3Dmol.Color();
        previousColorObj.setHex(previousColor);
        for (var i in atomsList) {
            var atomObject = atomsList[i];
            atomObject.color = initColorObj.getHex();
            if (previousArray1 && previousArray1.indexOf(atomObject.resi) !== -1) {
                atomObject.color = previousColorObj.getHex();
            }
            if (peptide1 && peptide1.indexOf(atomObject.resi) !== -1) {
                atomObject.color = colorObj.getHex();
            }
        }
    }

    if (pdbStr2 && pdbStr2.length > 10) {
        var n = glviewer.addModel(pdbStr2, "pdb", {doAssembly: true, duplicateAssemblyAtoms: true});
        n.setStyle({hetflag: false}, {cartoon: {}});
        var listofatoms = n.getAtoms();
        var colorObj2 = new $3Dmol.Color();
        colorObj2.setHex(selectedColor);
        var initColorObj2 = new $3Dmol.Color();
        initColorObj2.setHex(initialColor);
        var previousColorObj2 = new $3Dmol.Color();
        previousColorObj2.setHex(previousColor);
        for (var j in listofatoms) {
            var atomObject2 = listofatoms[j];
            atomObject2.color = initColorObj2.getHex();
            if (previousArray2 && previousArray2.indexOf(atomObject2.resi) !== -1) {
                atomObject2.color = previousColorObj2.getHex();
            }
            if (peptide2 && peptide2.indexOf(atomObject2.resi) !== -1) {
                atomObject2.color = colorObj2.getHex();
            }
        }
    }

    glviewer.zoomTo();
    glviewer.render();
}

function viewPDB(peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor) {
    renderDual3DModels(firstPDB, secondPDB, peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor);
}

function constructStructuresPDB() {
    var peptideArray1 = [0];
    var peptideArray2 = [0];
    var previousArray1 = [0];
    var previousArray2 = [0];
    viewPDB(peptideArray1, peptideArray2, previousArray1, previousArray2, "0xA9A9A9", "0xA9A9A9", "0xA9A9A9");
}

function constructStructures() {
    var peptideArray1 = [0];
    var peptideArray2 = [0];
    var previousArray1 = [0];
    var previousArray2 = [0];
    view($("#firstseq").val(), $("#secondseq").val(), peptideArray1, peptideArray2, previousArray1, previousArray2, "0xA9A9A9", "0xA9A9A9", "0xA9A9A9");
}

function view(pdbid_1, pdbid_2, peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor) {
    var id1 = (pdbid_1 || "3PGZ").toString().trim().toUpperCase();
    var id2 = (pdbid_2 || "3PGZ").toString().trim().toUpperCase();

    // If localPDB strings are available or in XLPM_PDB_LIBRARY, render immediately without network latency
    if (localFlag && firstPDB && secondPDB) {
        renderDual3DModels(firstPDB, secondPDB, peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor);
        return;
    }
    if (window.XLPM_PDB_LIBRARY && window.XLPM_PDB_LIBRARY[id1] && window.XLPM_PDB_LIBRARY[id2]) {
        firstPDB = window.XLPM_PDB_LIBRARY[id1];
        secondPDB = window.XLPM_PDB_LIBRARY[id2];
        renderDual3DModels(firstPDB, secondPDB, peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor);
        return;
    }

    // Fallback to HTTPS RCSB PDB download
    var appleUri = "https://files.rcsb.org/download/" + id1 + ".pdb";
    var pearUri = "https://files.rcsb.org/download/" + id2 + ".pdb";

    $.when($.get(appleUri), $.get(pearUri)).done(function (res1, res2) {
        firstPDB = res1[0];
        secondPDB = res2[0];
        renderDual3DModels(firstPDB, secondPDB, peptide1, peptide2, previousArray1, previousArray2, initialColor, previousColor, selectedColor);
    });
}

function loadPresetDataset(presetKey) {
    if (!window.XLPM_PRESETS || !window.XLPM_PRESETS[presetKey]) return;
    currentPresetId = presetKey;
    var preset = window.XLPM_PRESETS[presetKey];

    // Update active state on preset cards
    $(".preset-btn").removeClass("active-preset");
    $("#preset-" + presetKey).addClass("active-preset");

    // Populate metadata banner
    $("#active-preset-title").text(preset.title);
    $("#active-preset-badge").text(preset.badge);
    $("#active-preset-proteins").text(preset.proteins);
    $("#active-preset-pdb").text("PDB Models: " + preset.pdb1 + " × " + preset.pdb2);
    $("#active-preset-notes").text(preset.curationNotes);
    $("#drilldown-status").html("<strong>Level 1 Active (Global Peptide Matrix):</strong> Click any <span style='color:#1d4ed8;font-weight:700;'>blue cross-linked cell</span> in the matrix below to drill down into its MS/MS Precursor Spectral Treemap (Level 2).");

    // Load data into engine globals
    fastaText = preset.fasta;
    dataText = preset.data;
    $("#firstseq").val(preset.pdb1);
    $("#secondseq").val(preset.pdb2);
    firstPDB = (window.XLPM_PDB_LIBRARY && window.XLPM_PDB_LIBRARY[preset.pdb1]) ? window.XLPM_PDB_LIBRARY[preset.pdb1] : "";
    secondPDB = (window.XLPM_PDB_LIBRARY && window.XLPM_PDB_LIBRARY[preset.pdb2]) ? window.XLPM_PDB_LIBRARY[preset.pdb2] : "";
    localFlag = true;

    // Reset visualization canvas and run main()
    $("#vis").empty();
    main(fastaText, dataText);
}

$(document).ready(function () {
    // Wire optional custom file upload inputs for advanced users
    var fastafileInput = document.getElementById('fastafile');
    if (fastafileInput) {
        fastafileInput.addEventListener('change', function () {
            var file = fastafileInput.files[0];
            if (file) {
                var reader = new FileReader();
                reader.onload = function () {
                    fastaText = reader.result;
                };
                reader.readAsText(file);
            }
        });
    }

    var datafileInput = document.getElementById('datafile');
    if (datafileInput) {
        datafileInput.addEventListener('change', function () {
            var file = datafileInput.files[0];
            if (file) {
                var reader = new FileReader();
                reader.onload = function () {
                    dataText = reader.result;
                };
                reader.readAsText(file);
            }
        });
    }

    var firstPdbInput = document.getElementById('viewMol1');
    if (firstPdbInput) {
        firstPdbInput.addEventListener('change', function () {
            var file = firstPdbInput.files[0];
            if (file) {
                var reader = new FileReader();
                reader.onload = function () {
                    firstPDB = reader.result;
                    localFlag = true;
                };
                reader.readAsText(file);
            }
        });
    }

    var secondPdbInput = document.getElementById('viewMol2');
    if (secondPdbInput) {
        secondPdbInput.addEventListener('change', function () {
            var file = secondPdbInput.files[0];
            if (file) {
                var reader = new FileReader();
                reader.onload = function () {
                    secondPDB = reader.result;
                    localFlag = true;
                };
                reader.readAsText(file);
            }
        });
    }

    // Automatically load the default curated preset on page load
    setTimeout(function () {
        loadPresetDataset("rim1_dimer");
    }, 150);
});
