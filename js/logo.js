//Author: Islam Akef Ebeid

var geometry1, material1, mesh1;
var geometry2, material2, mesh2;
var geometry3, material3, mesh3;
var geometry4, material4, mesh4;
var geometry5, material5, mesh5;
var geometry6, material6, mesh6;
var scene, camera, renderer;
var targetRotationX = 0.01;
var targetRotationOnMouseDownX = 0.01;
var targetRotationY = 0.02;
var targetRotationOnMouseDownY = 0.02;
var mouseX = 0.01;
var mouseXOnMouseDown = 0.01;
var mouseY = 0.02;
var mouseYOnMouseDown = 0.02;
var windowHalfX = window.innerWidth / 2;
var windowHalfY = window.innerHeight / 2;
var half_the_width = document.getElementById("logo").offsetWidth / 2;
var region_length = half_the_width / 3;
var initial_region_in_half = region_length / 2;
var position1 = -(half_the_width - initial_region_in_half);
var position2 = position1 + region_length;
var position3 = position2 + region_length;
var position4 = position3 + region_length;
var position5 = position4 + region_length;
var position6 = position5 + region_length;

function letter(scene, charachter, position) {
    var canvas = document.createElement('canvas');
    var size = 200;
    canvas.width = size;
    canvas.height = size;
    var context = canvas.getContext('2d');
    context.fillStyle = '#000000';
    context.textAlign = 'center';
    context.font = '100px Helvetica';
    context.fillText(charachter, size / 2, size / 2);
    var amap = new THREE.Texture(canvas);
    amap.needsUpdate = true;
    var mat = new THREE.SpriteMaterial({
        map: amap,
        transparent: false,
        useScreenCoordinates: false,
        color: 0xffffff
    });
    var sp = new THREE.Sprite(mat);
    sp.scale.set(50, 50, 1);
    sp.position.set(position.x, position.y, position.z);
    scene.add(sp);
}

function init() {
    scene = new THREE.Scene();
    camera = new THREE.OrthographicCamera(document.getElementById("logo").offsetWidth / -2, document.getElementById("logo").offsetWidth / 2, document.getElementById("logo").offsetHeight / 2, document.getElementById("logo").offsetHeight / -2, 1, 10000);
    camera.position.z = 500;

    geometry1 = new THREE.BoxGeometry(30, 30, 30);
    material1 = new THREE.MeshBasicMaterial({color: 0x000000, wireframe: true});
    mesh1 = new THREE.Mesh(geometry1, material1);
    mesh1.position.set(position1, 10, 0);

    geometry2 = new THREE.BoxGeometry(30, 30, 30);
    material2 = new THREE.MeshBasicMaterial({color: 0x000000, wireframe: true});
    mesh2 = new THREE.Mesh(geometry2, material2);
    mesh2.position.set(position2, 10, 0);

    geometry3 = new THREE.BoxGeometry(30, 30, 30);
    material3 = new THREE.MeshBasicMaterial({color: 0x000000, wireframe: true});
    mesh3 = new THREE.Mesh(geometry3, material3);
    mesh3.position.set(position3, 10, 0);

    geometry4 = new THREE.BoxGeometry(30, 30, 30);
    material4 = new THREE.MeshBasicMaterial({color: 0x000000, wireframe: true});
    mesh4 = new THREE.Mesh(geometry4, material4);
    mesh4.position.set(position4, 10, 0);

    geometry5 = new THREE.BoxGeometry(30, 30, 30);
    material5 = new THREE.MeshBasicMaterial({color: 0x000000, wireframe: true});
    mesh5 = new THREE.Mesh(geometry5, material5);
    mesh5.position.set(position5, 10, 0);

    geometry6 = new THREE.BoxGeometry(30, 30, 30);
    material6 = new THREE.MeshBasicMaterial({color: 0x000000, wireframe: true});
    mesh6 = new THREE.Mesh(geometry6, material6);
    mesh6.position.set(position6, 10, 0);

    scene.add(mesh1);
    scene.add(mesh2);
    scene.add(mesh3);
    scene.add(mesh4);
    scene.add(mesh5);
    scene.add(mesh6);

    var position_i = {x: position1, y: 0, z: 0};
    letter(scene, "I", position_i);

    var position_3 = {x: position2, y: 0, z: 0};
    letter(scene, "3", position_3);

    var position_a = {x: position3, y: 0, z: 0};
    letter(scene, "A", position_a);

    var position_k = {x: position4, y: 0, z: 0};
    letter(scene, "K", position_k);

    var position_e = {x: position5, y: 0, z: 0};
    letter(scene, "E", position_e);

    var position_f = {x: position6, y: 0, z: 0};
    letter(scene, "F", position_f);

    renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
    renderer.setViewport(0, 0, document.getElementById("logo").offsetWidth, document.getElementById("logo").offsetHeight);
    renderer.setSize(document.getElementById("logo").offsetWidth, document.getElementById("logo").offsetHeight);
    renderer.setClearColor(0xffffff, 1);
    document.getElementById("logo").appendChild(renderer.domElement);
    window.addEventListener('resize', onWindowResize, false);
    document.addEventListener('mouseover', onDocumentMouseDown, false);
    document.addEventListener('touchstart', onDocumentTouchStart, false);
    document.addEventListener('touchmove', onDocumentTouchMove, false);
}

function onWindowResize() {
    camera.left = document.getElementById("logo").offsetWidth / -2;
    camera.right = document.getElementById("logo").offsetWidth / 2;
    camera.top = document.getElementById("logo").offsetHeight / 2;
    camera.bottom = document.getElementById("logo").offsetHeight / -2;
    camera.updateProjectionMatrix();
    renderer.setViewport(0, 0, document.getElementById("logo").offsetWidth, document.getElementById("logo").offsetHeight);
    renderer.setSize(document.getElementById("logo").offsetWidth, document.getElementById("logo").offsetHeight);
}

function onDocumentMouseDown(event) {
    event.preventDefault();
    document.addEventListener('mousemove', onDocumentMouseMove, false);
    document.addEventListener('mouseup', onDocumentMouseUp, false);
    document.addEventListener('mouseout', onDocumentMouseOut, false);
    mouseXOnMouseDown = event.clientX - windowHalfX;
    targetRotationOnMouseDownX = targetRotationX;
    mouseYOnMouseDown = event.clientY - windowHalfY;
    targetRotationOnMouseDownY = targetRotationY;
}

function onDocumentMouseMove(event) {
    mouseX = event.clientX - windowHalfX;
    mouseY = event.clientY - windowHalfY;
    targetRotationY = targetRotationOnMouseDownY + (mouseY - mouseYOnMouseDown) * 0.001;
    targetRotationX = targetRotationOnMouseDownX + (mouseX - mouseXOnMouseDown) * 0.001;
}

function onDocumentMouseUp(event) {
    document.removeEventListener('mousemove', onDocumentMouseMove, false);
    document.removeEventListener('mouseup', onDocumentMouseUp, false);
    document.removeEventListener('mouseout', onDocumentMouseOut, false);
}

function onDocumentMouseOut(event) {
    document.removeEventListener('mousemove', onDocumentMouseMove, false);
    document.removeEventListener('mouseup', onDocumentMouseUp, false);
    document.removeEventListener('mouseout', onDocumentMouseOut, false);
}

function onDocumentTouchStart(event) {
    if (event.touches.length === 1) {
        event.preventDefault();
        mouseXOnMouseDown = event.touches[ 0 ].pageX - windowHalfX;
        targetRotationOnMouseDownX = targetRotationX;
        mouseYOnMouseDown = event.touches[ 0 ].pageY - windowHalfY;
        targetRotationOnMouseDownY = targetRotationY;
    }
}

function onDocumentTouchMove(event) {
    if (event.touches.length === 1) {
        event.preventDefault();
        mouseX = event.touches[ 0 ].pageX - windowHalfX;
        targetRotationX = targetRotationOnMouseDownX + (mouseX - mouseXOnMouseDown) * 0.05;
        mouseY = event.touches[ 0 ].pageY - windowHalfY;
        targetRotationY = targetRotationOnMouseDownY + (mouseY - mouseYOnMouseDown) * 0.05;
    }
}

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
    mesh1.rotation.x = targetRotationX;
    mesh1.rotation.y = targetRotationY;
    mesh2.rotation.x = targetRotationX;
    mesh2.rotation.y = targetRotationY;
    mesh3.rotation.x = targetRotationX;
    mesh3.rotation.y = targetRotationY;
    mesh4.rotation.x = targetRotationX;
    mesh4.rotation.y = targetRotationY;
    mesh5.rotation.x = targetRotationX;
    mesh5.rotation.y = targetRotationY;
    mesh6.rotation.x = targetRotationX;
    mesh6.rotation.y = targetRotationY;
}

function main() {
    init();
    animate();
}