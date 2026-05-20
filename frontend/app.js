const BASE_URL = "https://imagesticker.onrender.com";

// --------------------
// ELEMENTS
// --------------------

let isProcessing = false;

const sidebar = document.getElementById("sidebar");
const menuBtn = document.getElementById("menuBtn");
const closeBtn = document.getElementById("closeBtn");

const preview = document.getElementById("preview");
const uploadFile = document.getElementById("uploadFile");

const size = document.getElementById("size");
const rotate = document.getElementById("rotate");
const border = document.getElementById("border");
const borderColor = document.getElementById("borderColor");
const brightness = document.getElementById("brightness");
const contrast = document.getElementById("contrast");
const saturate = document.getElementById("saturate");
const blur = document.getElementById("blur");

const style = document.getElementById("style");

const fullBtn = document.getElementById("fullBtn");
const faceBtn = document.getElementById("faceBtn");
const generateBtn = document.getElementById("generateBtn");
const resetBtn = document.getElementById("resetBtn");

let imageUploaded = false;
let currentFile = null;
let currentMode = "full";
let currentBlobUrl = null;  


function showToast(message = "✔ Done") {

    const toast = document.getElementById("toast");
    if (!toast) return;

    toast.innerText = message;

    // show
    toast.classList.remove("hidden");

    // auto hide
    setTimeout(() => {
        toast.classList.add("hidden");
    }, 2000);
}

// --------------------
// SIDEBAR
// --------------------
if (menuBtn && sidebar && closeBtn) {
    menuBtn.addEventListener("click", () => sidebar.classList.remove("hidden-sidebar"));
    closeBtn.addEventListener("click", () => sidebar.classList.add("hidden-sidebar"));
}

// --------------------
// LOADING UI
// --------------------
const loader = document.getElementById("loader");
const statusBox = document.getElementById("statusBox");
const statusText = document.getElementById("statusText");

function setLoading(state, text = "Processing image...") {

    if (!loader || !statusBox) return;

    const uploadBox = document.getElementById("uploadBox");

    if (state) {
        loader.classList.remove("hidden");
        statusBox.classList.remove("hidden");
        statusText.innerText = text;

        uploadBox?.classList.add("opacity-50", "pointer-events-none");
    } else {
        loader.classList.add("hidden");
        statusBox.classList.add("hidden");

        uploadBox?.classList.remove("opacity-50", "pointer-events-none");
    }
}

// --------------------
// SAFE NUMBER HELPER
// --------------------
function safeNumber(val, fallback = 0) {
    const n = Number(val);
    return isNaN(n) ? fallback : n;
}

// --------------------
// PREVIEW
// --------------------
function showPreview(imageUrl) {

    const img = document.getElementById("preview");
    const text = document.getElementById("previewText");

    if (!imageUrl) return;

    const finalUrl = getFullUrl(imageUrl);

    // IMPORTANT: force reset
    img.classList.add("hidden");
    img.src = "";

    setTimeout(() => {

        img.onload = () => {
            text.classList.add("hidden");
            img.classList.remove("hidden");
        };

        img.onerror = () => {
            text.classList.remove("hidden");
        };

        img.src = finalUrl;

    }, 50);
}

function getFullUrl(url) {
    if (!url) return "";

    return url.startsWith("http") || url.startsWith("blob:")
        ? url
        : `${BASE_URL}${url.startsWith("/") ? "" : "/"}${url}`;
}
// --------------------
// MODE UI
// --------------------
function updateModeButtons(mode) {

    if (!fullBtn || !faceBtn) {
        console.log("Mode buttons not found on this page");
        return;
    }

    [fullBtn, faceBtn].forEach(btn => {
        btn.className = btn.className
            .replace(/bg-\S+/g, "")
            .replace(/text-\S+/g, "");

        btn.classList.add("bg-white", "text-black");
    });

    const activeBtn = mode === "full" ? fullBtn : faceBtn;

    activeBtn.classList.remove("bg-white", "text-black");
    activeBtn.classList.add("bg-blue-500", "text-white");
}

// --------------------
// FILE UPLOAD
// --------------------
if(uploadFile){
uploadFile.addEventListener("change", function () {

    if (isProcessing) return;

    const file = this.files[0];
    if (!file) return;

    currentFile = file;

    if (currentBlobUrl) {
        URL.revokeObjectURL(currentBlobUrl);
    }

    currentBlobUrl = URL.createObjectURL(file);
    showPreview(currentBlobUrl);

    imageUploaded = true;

    showToast("Image loaded ✔");

    resetBtn?.classList.add("hidden");
});
}

if(generateBtn){
generateBtn?.addEventListener("click", async () => {

    if (!currentFile) {
        alert("Upload image first");
        return;
    }

    await sendToBackend(currentMode);
});
}

if(resetBtn){
resetBtn?.addEventListener("click", () => {

    uploadFile.value = "";
    currentFile = null;
    imageUploaded = false;

    preview.src = "";
    preview.classList.add("hidden");

    document.getElementById("previewText")?.classList.remove("hidden");

    blur.value = 0;
    saturate.value = 100;
    brightness.value = 100;
    contrast.value = 100;
    rotate.value = 0;
    border.value = 0;

    style.value = "";
    document.getElementById("borderStyle").value = "simple";
    borderColor.value = "#000000";

    document.getElementById("facesContainer").innerHTML = "";
    document.getElementById("facesContainer").classList.add("hidden");

    resetBtn.classList.add("hidden");

    showToast("Reset done ✔");
    if (currentBlobUrl) {
        URL.revokeObjectURL(currentBlobUrl);
        currentBlobUrl = null;
    }
});
}

// --------------------
// BACKEND CALL
// --------------------
async function sendToBackend(mode = "full") {

    if (!currentFile || isProcessing) return;

    isProcessing = true;
    setLoading(true, "Processing image...");

    const formData = new FormData();

    formData.append("file", currentFile);
    formData.append("mode", mode);
    formData.append("style", style?.value || "");

    formData.append("brightness", safeNumber(brightness?.value, 100));
    formData.append("contrast", safeNumber(contrast?.value, 100));
    formData.append("rotate", safeNumber(rotate?.value, 0));
    formData.append("saturate", safeNumber(saturate?.value, 100));
    formData.append("blur", safeNumber(blur?.value, 0));
    formData.append("border_size", safeNumber(border?.value, 0));
    formData.append("border_color", borderColor?.value || "#000000");

    formData.append(
        "border_style",
        document.getElementById("borderStyle")?.value || "simple"
    );

    try {
        const token = localStorage.getItem("token");

        const headers = {};

        if (token) {
            headers["Authorization"] = `Bearer ${token}`;
        }

        const res = await fetch(`${BASE_URL}/api/process/`, {
            method: "POST",
            headers,
            body: formData
        });

        // Backend error
        if (!res.ok) {
            throw new Error(`Server error ${res.status}`);
        }

        const data = await res.json();

        // Empty response check
        if (!data || (!data.url && !data.faces)) {
            throw new Error("No output received");
        }

        // --------------------
        // MAIN IMAGE PREVIEW
        // --------------------
        if (data.url) {

            showPreview(data.url);
        } else {
            console.warn("No main image URL found");
        }

        resetBtn?.classList.remove("hidden");

        // --------------------
        // FACE MODE
        // --------------------
        if (mode === "face") {
        
            if (data.faces?.length > 0) {
        
                const container = document.getElementById("facesContainer");
        
                container.innerHTML = "";
        
                // Always show first face in center
                showPreview(data.faces[0].face_url);
        
                // Only show selector for multiple faces
                if (data.faces.length > 1) {
        
                    container.classList.remove("hidden");
        
                    data.faces.forEach((f, index) => {
        
                        const img = document.createElement("img");
        
                        img.src = getFullUrl(f.face_url);
        
                        img.className = `
                            w-20 h-20 rounded-xl object-cover cursor-pointer
                            border border-transparent hover:border-blue-500
                        `;
        
                        img.onclick = () => {
                            showPreview(f.face_url);
                        };
        
                        container.appendChild(img);
                    });
        
                } else {
                    container.classList.add("hidden");
                }
        
            } else {
                console.warn("No faces received");
            }
        }

        showToast("Generated ✔");

    } catch (err) {

        console.log("ERROR MESSAGE:", err.message);
    
        if (err.name === "AbortError") {
            showToast("Server timeout. Try again.");
        } else {
            showToast(err.message || "Processing failed. Try again.");
        }
    } finally {
        setLoading(false);
        isProcessing = false;

    }
}

// --------------------
// LIVE FILTERS
// --------------------
function updateSticker() {

    if (!imageUploaded) return;
    

    const blurVal = safeNumber(blur?.value, 0);
    const satVal = safeNumber(saturate?.value, 100);
    const brightVal = safeNumber(brightness?.value, 100);
    const contrastVal = safeNumber(contrast?.value, 100);
    const rotateVal = safeNumber(rotate?.value, 0);
    const borderStyle = document.getElementById("borderStyle")?.value || "simple";
    const borderSize = safeNumber(border?.value, 0);
    const borderColorVal = borderColor?.value || "#000000";

    preview.style.width = size?.value ? size.value + "px" : "auto";
    preview.style.transform = `rotate(${rotateVal}deg)`;

    preview.style.filter = `
        brightness(${brightVal}%)
        contrast(${contrastVal}%)
        saturate(${satVal}%)
        blur(${blurVal}px)
    `;

    preview.style.border = `${borderSize}px ${borderStyle} ${borderColorVal}`;
}

// --------------------
// INPUT LISTENERS
// --------------------
document.querySelectorAll("input, select").forEach(el => {
    el.addEventListener("input", updateSticker);
});

// --------------------
// MODE SWITCH
// --------------------
window.setMode = async function (mode) {
    currentMode = mode;
    updateModeButtons(mode);
};

if (fullBtn && faceBtn) {
    updateModeButtons(currentMode);
}

function go(id) {

    // Reset all section headings
    document.querySelectorAll("section h2").forEach(h => {
        h.classList.remove("text-blue-600");
    });

    // Find section
    const section = document.getElementById(id);

    if (!section) {
        return;
    }

    // Find h2 inside that section
    const heading = section.querySelector("h2");

    // Make heading orange
    if (heading) {
        heading.classList.add("text-blue-600");
    }

    // Scroll
    window.scrollTo({
        top: section.offsetTop - 100,
        behavior: "smooth"
    });
}

function toggleText(id, btn) {

    const text = document.getElementById(id);

    if (text.classList.contains("line-clamp-2")) {
        text.classList.remove("line-clamp-2");
        btn.innerText = "Read Less";
    } else {
        text.classList.add("line-clamp-2");
        btn.innerText = "Read More";
    }

}

document.addEventListener("DOMContentLoaded", () => {

    // ---------------- LOGIN ----------------
    const loginBtn = document.getElementById("loginBtn");

    if (loginBtn) {
        loginBtn.addEventListener("click", async (e) => {
            e.preventDefault();

            const email = document.getElementById("loginEmail").value.trim();
            const password = document.getElementById("loginPassword").value.trim();

            const response = await fetch(`${BASE_URL}/api/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const data = await response.json();

            console.log("LOGIN RESPONSE:", data);

            if (data.access_token) {
                localStorage.setItem("token", data.access_token);
                console.log("TOKEN SAVED:", localStorage.getItem("token"));

                window.location.href = "dashboard.html";
            }
        });
    }

    // ---------------- REGISTER ----------------
    const registerBtn = document.getElementById("registerBtn");

    if (registerBtn) {
        registerBtn.addEventListener("click", async () => {

            const name = document.getElementById("name")?.value.trim();
            const email = document.getElementById("email")?.value.trim();
            const password = document.getElementById("password")?.value.trim();

            const response = await fetch(`${BASE_URL}/api/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, email, password })
            });

            const data = await response.json();

            if (response.ok) {
                window.location.href = "login.html";
            } else {
                alert(data.message);
            }
        });
    }

    // ---------------- DASHBOARD LOADERS ----------------
    if (document.getElementById("favoritesContainer")) loadFavorites();
    if (document.getElementById("stickersContainer")) loadMyStickers();
    if (document.getElementById("collectionsContainer")) loadCollections();
    if (document.getElementById("deletedContainer")) loadDeleted();

    initCircle();

    if (window.location.pathname.includes("dashboard.html")) {
        loadUserProfile();
    }

    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }

});



function initCircle() {

    const wrapper = document.getElementById("circleWrapper");
    if (!wrapper) return;

    const images = document.querySelectorAll(".circle-img");
    const leftBtn = document.getElementById("leftBtn");
    const rightBtn = document.getElementById("rightBtn");

    let rotation = 0;

    function updateCircle() {

        const size = wrapper.offsetWidth;

        const centerX = size / 2;
        const centerY = size / 2;

        const radius = size * 0.25;

        images.forEach((img, index) => {

            const angle =
                (index * (360 / images.length) + rotation)
                * Math.PI / 180;

            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);

            img.style.left = `${x - img.offsetWidth / 2}px`;
            img.style.top = `${y - img.offsetHeight / 2}px`;
        });
    }

    leftBtn?.addEventListener("click", () => {
        rotation -= 72;
        updateCircle();
    });

    rightBtn?.addEventListener("click", () => {
        rotation += 72;
        updateCircle();
    });

    updateCircle();
}

fetch("footer.html")
.then(res => res.text())
.then(data => {

    const footer = document.getElementById("footer");

    if (!footer) {
        console.log("footer div not found");
        return;
    }

    footer.innerHTML = data;
});

const downloadBtn = document.getElementById("downloadBtn");

if (downloadBtn) {
    downloadBtn.addEventListener("click", () => {

        if (!preview.src) {
            showToast("No image to download");
            return;
        }

        const a = document.createElement("a");
        a.href = preview.src;
        a.download = "stickerspark.png";
        a.click();
    });
}

const shareBtn = document.getElementById("shareBtn");

if (shareBtn) {
    shareBtn.addEventListener("click", async () => {

        if (!preview.src) {
            showToast("No image to share");
            return;
        }

        try {
            // 1. fetch image as blob
            const response = await fetch(preview.src);
            const blob = await response.blob();

            // 2. convert blob → file
            const file = new File([blob], "stickerspark.png", {
                type: blob.type
            });

            // 3. check share support
            if (navigator.canShare && navigator.canShare({ files: [file] })) {

                await navigator.share({
                    title: "My Sticker",
                    text: "Check out my generated sticker!",
                    files: [file]
                });

            } else {
                showToast("Sharing images not supported on this device/browser");
            }

        } catch (err) {
            showToast("Failed to share image");
        }

    });
}

async function loadUserProfile() {

    const token = localStorage.getItem("token");

    const response = await fetch(`${BASE_URL}/api/auth/profile`, {
        method: "GET",
        headers: {
            "Authorization": `Bearer ${token}`
        }
    });

    if (!response.ok) {
        console.log("Profile fetch failed");
        return;
    }

    const user = await response.json();

    document.getElementById("userName").innerText = user.name || "User";
    document.getElementById("userEmail").innerText = user.email || "";
}

async function loadMyStickers() {

    try {

        const response = await fetch(
            `${BASE_URL}/api/outputs`
        );

        const data = await response.json();

        const container =
            document.getElementById("stickersContainer");

        if (!container) return;

        container.innerHTML = "";

        //  EMPTY STATE CHECK (ADD THIS)
        if (!data.urls || data.urls.length === 0) {

            container.innerHTML = `
                <div class="col-span-full flex flex-col items-center justify-center w-full min-h-[300px] text-gray-700">

                    <p class="text-xl font-semibold mb-4">No stickers yet</p>
                    <p class="text-lg mt-1 flex items-center justify-center gap-6">
                    Start uploading 
                    <i data-lucide="upload" class="w-8 h-8 text-blue-500"></i>
                    your stickers
                    </p>

                </div>
            `;

            if (typeof lucide !== "undefined") {
                lucide.createIcons();
            }
            return;
        }

        // render stickers if available
        data.urls.reverse().forEach(url => {

            const card =
                document.createElement("div");

            card.className =
                "bg-white rounded-2xl shadow-md p-3";

                card.innerHTML = `
    
                <img src="${url}"
                class="w-full h-48 object-contain rounded-xl bg-gray-50 p-2">
            
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-2 mt-3">
            
                    <button onclick="addToCollection('${url}')" 
                    class="w-full p-3 bg-orange-500 text-white rounded-lg grid place-items-center">
            
                        <div class="flex items-center justify-center gap-2 w-full">
                            <i data-lucide="folder-plus" class="w-4 h-4"></i>
                            <span class="text-center w-full">Collection</span>
                        </div>
            
                    </button>
            
                    <button onclick="addToFavorites('${url}')" 
                    class="w-full px-3 py-2 bg-pink-500 text-white rounded-lg grid place-items-center">
            
                        <div class="flex items-center justify-center gap-2 w-full">
                            <i data-lucide="heart" class="w-4 h-4"></i>
                            <span class="text-center w-full">Favorite</span>
                        </div>
            
                    </button>
            
                    <button onclick="deleteSticker('${url}', 'myStickers')" 
                    class="w-full px-3 py-2 bg-red-500 text-white rounded-lg grid place-items-center">
            
                        <div class="flex items-center justify-center gap-2 w-full">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                            <span class="text-center w-full">Delete</span>
                        </div>
            
                    </button>
            
                </div>
            `;
            container.appendChild(card);
        });
        if (typeof lucide !== "undefined") {
            lucide.createIcons();
        }

    } catch(error) {

        console.log(
            "Sticker loading error:",
            error
        );

    }
}

const favoriteBtn = document.getElementById("favoriteBtn");
if(favoriteBtn){
    favoriteBtn.addEventListener("click", () => {

        if (!preview.src) return;
    
        let favorites =
            JSON.parse(
                localStorage.getItem("favorites")
            ) || [];
    
        favorites.push(preview.src);
    
        localStorage.setItem(
            "favorites",
            JSON.stringify(favorites)
        );
    
        alert("Added to favorites");
    
    });
}

function loadFavorites() {

    const favorites =
        JSON.parse(
            localStorage.getItem("favorites")
        ) || [];

    const container =
        document.getElementById(
            "favoritesContainer"
        );

    if (!container) return;

    container.innerHTML = "";

    //  EMPTY STATE CHECK (ADD THIS)
    if (favorites.length === 0) {

        container.innerHTML = `
            <div class="col-span-full flex flex-col items-center justify-center w-full min-h-[300px] text-gray-700">

                <p class="text-xl font-semibold mb-4">No favorites yet</p>
                <p class="text-lg mt-1 flex items-center justify-center gap-6">Tap <i data-lucide="heart" class="w-8 h-8 text-red-500"></i> on stickers you like</p>

            </div>
        `;
        if (typeof lucide !== "undefined") {
            lucide.createIcons();
        }

        return;
    }

    // 🔥 render favorites
    favorites.reverse().forEach(url => {

        const card =
            document.createElement("div");

        card.className =
            "bg-white rounded-2xl shadow-md p-3";

            card.innerHTML = `
    
            <img src="${url}"
            class="w-full h-48 object-contain rounded-xl bg-gray-50 p-2">
        
            <div class="grid grid-cols-2 gap-2 mt-3">
        
                <button
                    onclick="addToCollection('${url}')"
                    class="w-full px-3 py-2 bg-orange-500 text-white rounded-lg flex items-center justify-center gap-2">
        
                    <i data-lucide="folder-plus" class="w-4 h-4"></i>
                    <span>Collection</span>
        
                </button>
        
                <button
                    onclick="deleteSticker('${url}', 'favorites')"
                    class="w-full px-3 py-2 bg-red-500 text-white rounded-lg flex items-center justify-center gap-2">
        
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                    <span>Delete</span>
        
                </button>
        
            </div>
        `;
        container.appendChild(card);

    });

    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }
}

function loadCollections() {

    const collections =
        JSON.parse(
            localStorage.getItem("collections")
        ) || {};

    const container =
        document.getElementById(
            "collectionsContainer"
        );

    if (!container) return;

    container.innerHTML = "";

    // EMPTY STATE CHECK (IMPORTANT)
    if (Object.keys(collections).length === 0) {

        container.innerHTML = `
            <div class="col-span-full flex flex-col items-center justify-center w-full min-h-[300px] text-gray-700">

                <p class="text-xl font-semibold mb-4">No collections yet</p>
                <p class="text-lg mt-1 flex items-center justify-center gap-6">
                Create your first <i data-lucide="folder" class="w-8 h-8 text-orange-400"></i> collection</p>

            </div>
        `;
        if (typeof lucide !== "undefined") {
            lucide.createIcons();
        }

        return;
    }

    // 🔥 render collections
    Object.keys(collections).forEach(name => {

        const section =
            document.createElement("div");

        section.className = "mb-8";

        let stickersHtml = "";

        collections[name].forEach(url => {

            stickersHtml += `
            <div class="bg-white rounded-2xl shadow-md p-3">

            <img src="${url}" class="w-full h-48 object-contain rounded-xl bg-gray-50 p-2">

            <div class="grid grid-cols-2 gap-2 mt-3">
            <button
                onclick="addToFavorites('${url}')"
                class="w-full px-3 py-2 bg-pink-500 text-white rounded-lg flex items-center justify-center gap-2">

                <i data-lucide="heart" class="w-4 h-4"></i>
                <span>Favorite</span>

            </button>

            <button
                onclick="deleteSticker('${url}', 'collections')"
                class="w-full px-3 py-2 bg-red-500 text-white rounded-lg flex items-center justify-center gap-2">

                <i data-lucide="trash-2" class="w-4 h-4"></i>
                <span>Delete</span>

            </button>

            </div>

            </div>`;
        
        });

        section.innerHTML = `
        
            <h2 class="text-xl font-bold mb-4 text-orange-500">
                ${name}
            </h2>

            <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                ${stickersHtml}
            </div>
        `;

        container.appendChild(section);

    });
    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }
}

window.addToFavorites = function addToFavorites(url) {

    let favorites =
        JSON.parse(
            localStorage.getItem("favorites")
        ) || [];

    // Avoid duplicates
    if (!favorites.includes(url)) {
        favorites.push(url);
    }

    localStorage.setItem(
        "favorites",
        JSON.stringify(favorites)
    );

    showToast("Added to favorites");
}

window.addToCollection = function addToCollection(url) {

    const collectionName =
        prompt("Enter collection name");

    if (!collectionName) return;

    let collections =
        JSON.parse(
            localStorage.getItem("collections")
        ) || {};

    // Create collection if not exists
    if (!collections[collectionName]) {
        collections[collectionName] = [];
    }

    // Avoid duplicates
    if (!collections[collectionName].includes(url)) {
        collections[collectionName].push(url);
    }

    localStorage.setItem(
        "collections",
        JSON.stringify(collections)
    );

    showToast("Added to collection");
}

window.deleteSticker = async function deleteSticker(url, source) {

    // Add to deleted
    let deleted =
        JSON.parse(
            localStorage.getItem("deleted")
        ) || [];

    if (!deleted.includes(url)) {
        deleted.push(url);
    }

    localStorage.setItem(
        "deleted",
        JSON.stringify(deleted)
    );

    // Remove from myStickers
    if (source === "myStickers") {

        await fetch(`${BASE_URL}/api/outputs`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({ url })
        });
    
    }

    // Remove from favorites
    if (source === "favorites") {

        let favorites =
            JSON.parse(
                localStorage.getItem("favorites")
            ) || [];

        favorites =
            favorites.filter(
                img => img !== url
            );

        localStorage.setItem(
            "favorites",
            JSON.stringify(favorites)
        );
    }

    // Remove from collections
    if (source === "collections") {

        let collections =
            JSON.parse(
                localStorage.getItem("collections")
            ) || {};

        Object.keys(collections).forEach(name => {

            collections[name] =
                collections[name].filter(
                    img => img !== url
                );

        });

        localStorage.setItem(
            "collections",
            JSON.stringify(collections)
        );
    }

    showToast("Moved to deleted");

    if (document.getElementById("favoritesContainer")) {
        loadFavorites();
    }
    
    if (document.getElementById("collectionsContainer")) {
        loadCollections();
    }
    
    if (document.getElementById("stickersContainer")) {
        loadMyStickers();
    }
}

function loadDeleted() {

    const deleted =
        JSON.parse(
            localStorage.getItem("deleted")
        ) || [];

    const container =
        document.getElementById(
            "deletedContainer"
        );

    if (!container) return;

    container.innerHTML = "";

    //  EMPTY STATE CHECK (ADD THIS)
    if (deleted.length === 0) {

        container.innerHTML = `
            <div class="col-span-full flex flex-col items-center justify-center w-full min-h-[300px] text-gray-700">

                <p class="text-xl font-semibold mb-4">No deleted stickers</p>
                <p class="text-lg mt-1 flex items-center justify-center gap-6">
                Deleted <i data-lucide="trash-2" class="w-8 h-8 text-gray-400"></i> stickers will appear here</p>

            </div>
        `;
        if (typeof lucide !== "undefined") {
            lucide.createIcons();
        }
        return;
    }

    // 🔥 render deleted stickers
    deleted.reverse().forEach(url => {

        const card =
            document.createElement("div");

        card.className =
            "bg-white rounded-2xl shadow-md p-3";

        card.innerHTML = `
        
            <img src="${url}"
            class="w-full h-48 object-contain rounded-xl bg-gray-50 p-2">

            <div class="flex justify-center gap-2 mt-3">

                <button
                    onclick="restoreSticker('${url}')"
                    class="px-3 py-2 bg-green-500 text-white rounded-lg flex items-center gap-2">

                    <i data-lucide="rotate-ccw"></i>
                    Restore

                </button>

                <button
                    onclick="deleteForever('${url}')"
                    class="px-3 py-2 bg-red-500 text-white rounded-lg flex items-center gap-2">

                    <i data-lucide="trash-2"></i>
                    Delete

                </button>

            </div>
        `;

        container.appendChild(card);

    });

    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }
}

function restoreSticker(url) {

    try {

        let deleted =
            JSON.parse(localStorage.getItem("deleted")) || [];

        // remove from deleted
        deleted = deleted.filter(item => item !== url);

        localStorage.setItem("deleted", JSON.stringify(deleted));

        showToast("Sticker restored");

        loadDeleted();

    } catch (err) {
        console.error("restoreSticker error:", err);
    }
}

function deleteForever(url) {

    try {

        let deleted =
            JSON.parse(localStorage.getItem("deleted")) || [];

        deleted = deleted.filter(item => item !== url);

        localStorage.setItem("deleted", JSON.stringify(deleted));

        showToast("Deleted permanently");

        loadDeleted();

    } catch (err) {
        console.error("deleteForever error:", err);
    }
}



