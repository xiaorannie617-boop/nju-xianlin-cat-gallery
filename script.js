let cats = [];


// ======================================================
// 读取猫咪数据库
// ======================================================

fetch("cats_detail.json")
    .then(response => {

        if (!response.ok) {
            throw new Error(
                "cats_detail.json 读取失败，HTTP状态码：" + response.status
            );
        }

        return response.json();
    })

    .then(data => {

        // 确保读取到的是数组
        if (!Array.isArray(data)) {

            throw new Error(
                "cats_detail.json 的数据格式不是数组"
            );

        }

        cats = data;

        console.log(
            "猫苑数据库加载成功，共",
            cats.length,
            "只猫咪",
            cats
        );


        // ==============================
        // 更新猫咪数量
        // ==============================

        const count =
            document.getElementById("catCount");

        if (count) {

            count.innerHTML = cats.length;

        }


        // ==============================
        // 显示全部猫咪
        // ==============================

       createAreaButtons();

       showCats();

       loadMapMarkers();

    })

    .catch(error => {

        console.error(
            "猫咪数据库读取失败：",
            error
        );


        // 如果数据库读取失败
        // 页面不要继续显示“0只猫咪”造成误解

        const count =
            document.getElementById("catCount");

        if (count) {

            count.innerHTML = "读取失败";

        }


        const box =
            document.getElementById("catList");

        if (box) {

            box.innerHTML = `
                <div class="record">
                    <h3>⚠️ 猫咪数据库读取失败</h3>
                    <p>
                        请打开浏览器控制台查看详细错误。
                    </p>
                    <p>
                        错误信息：
                        ${error.message}
                    </p>
                </div>
            `;

        }

    });




// ======================================================
// 显示全部猫咪
// ======================================================

// ======================================================
// 自动生成活动区域按钮
// ======================================================

function createAreaButtons() {

    const box =
        document.getElementById("areaButtons");


    if (!box) {

        console.warn(
            "没有找到 areaButtons"
        );

        return;

    }


    // ==========================================
    // 获取所有活动区域
    // ==========================================

    const areas = [
        ...new Set(

            cats

                .map(cat => cat["活动区域"])

                .filter(area =>
                    area &&
                    area.trim() !== ""
                )

        )
    ];


    // ==========================================
    // 全部猫咪按钮
    // ==========================================

    let html = `

        <button
            class="area-button active"
            onclick="filterCats('全部')"
        >
            全部
        </button>

    `;


    // ==========================================
    // 各个区域按钮
    // ==========================================

    areas.forEach(area => {

        html += `

            <button
                class="area-button"
                onclick="filterCats('${escapeHtmlAttribute(area)}')"
            >
                ${escapeHtml(area)}
            </button>

        `;

    });


    box.innerHTML = html;

}

// ======================================================
// 按活动区域筛选猫咪
// ======================================================

function filterCats(area) {

    const buttons =
        document.querySelectorAll(
            ".area-button"
        );


    // ==========================================
    // 更新按钮状态
    // ==========================================

    buttons.forEach(button => {

        button.classList.remove("active");

    });


    // 找到当前点击的按钮

    buttons.forEach(button => {

        if (
            button.innerText.trim() === area
        ) {

            button.classList.add("active");

        }

    });


    // ==========================================
    // 全部猫咪
    // ==========================================

    if (area === "全部") {

        showCats();

        // 地图显示全部猫咪
        loadMapMarkers();

        return;

    }


    // ==========================================
    // 筛选猫咪
    // ==========================================

    const filteredCats =
        cats.filter(
            cat =>
                cat["活动区域"] === area
        );


    // 更新猫咪列表
    showCats(filteredCats);


    // ==========================================
    // 更新地图
    // ==========================================

    loadMapMarkers(filteredCats);

}

function showCats(catList = cats) {

    const box =
        document.getElementById("catList");


    if (!box) {

        console.warn(
            "没有找到 id='catList' 的元素"
        );

        return;

    }


    let html = "";


    catList.forEach(cat => {

        html += `

            <div
                class="cat-card"
                onclick="openCat('${escapeHtmlAttribute(cat["名字"] || "")}')"
            >

                <img
                    src="images/${escapeHtmlAttribute(cat["照片"] || "default.jpg")}"
                    alt="${escapeHtmlAttribute(cat["名字"] || "猫咪")}"
                    onerror="this.onerror=null; this.src='images/default.jpg';"
                >


                <h3>
                    🐱 ${escapeHtml(cat["名字"] || "未命名猫咪")}
                </h3>


                <!-- 猫咪标签 -->

                <div class="cat-tags">

                    ${
                        cat["毛色"]
                        ?
                        `
                        <span class="cat-tag">
                            🎨 ${escapeHtml(cat["毛色"])}
                        </span>
                        `
                        :
                        ""
                    }


                    ${
                        cat["体型"]
                        ?
                        `
                        <span class="cat-tag">
                            📏 ${escapeHtml(cat["体型"])}
                        </span>
                        `
                        :
                        ""
                    }


                    ${
                        cat["性格"]
                        ?
                        `
                        <span class="cat-tag">
                            💕 ${escapeHtml(cat["性格"])}
                        </span>
                        `
                        :
                        ""
                    }

                </div>


                <!-- 活动区域 -->

                ${
                    cat["活动区域"]
                    ?
                    `
                    <div class="cat-card-area">
                        📍 ${escapeHtml(cat["活动区域"])}
                    </div>
                    `
                    :
                    ""
                }


                <!-- 常见行为 -->

                ${
                    cat["常见行为"]
                    ?
                    `
                    <div class="cat-card-behavior">
                        ${escapeHtml(cat["常见行为"])}
                    </div>
                    `
                    :
                    ""
                }


                <div class="cat-card-more">
                    查看完整档案 →
                </div>

            </div>

        `;

    });


    box.innerHTML = html;

}




// ======================================================
// 点击猫咪卡片
// ======================================================

function openCat(name) {

    const cat = cats.find(
        item => item["名字"] === name
    );

    if (!cat) {
        return;
    }

    window.location.href = `detail.html?id=${cat.id}`;
}




// ======================================================
// 搜索猫咪
// ======================================================

function searchCat() {

    const input =
        document.getElementById("catName");


    const result =
        document.getElementById("result");


    if (!input || !result) {

        console.warn(
            "没有找到搜索框或结果区域"
        );

        return;

    }


    const name =
        input.value.trim();


    // 没有输入名字

    if (!name) {

        result.innerHTML = `
            <div class="record">
                <h3>🐱 请输入猫咪名字</h3>
            </div>
        `;

        return;

    }


    // ==============================
    // 查找猫咪
    // ==============================

    const cat =
        cats.find(
            item =>
                item["名字"] === name
        );


    // ==============================
    // 没找到
    // ==============================

    if (!cat) {

        result.innerHTML = `

            <div class="record">

                <h3>
                    没有找到这只猫咪
                </h3>

                <p>
                    当前数据库共有
                    ${cats.length}
                    只猫咪。
                </p>

            </div>

        `;

        return;

    }


    // ==================================================
    // 猫咪基本信息
    // ==================================================

    let html = `

        <div class="record">

            <h2>
                🐱 ${escapeHtml(cat["名字"] || "未命名猫咪")}
            </h2>


            <img
                src="images/${escapeHtmlAttribute(cat["照片"] || "default.jpg")}"
                alt="${escapeHtmlAttribute(cat["名字"] || "猫咪")}"
                style="
                    width:200px;
                    border-radius:15px;
                    display:block;
                    margin:15px auto;
                "
                onerror="this.onerror=null; this.src='images/default.jpg';"
            >


            <p>
                <b>活动区域：</b>
                ${escapeHtml(cat["活动区域"] || "暂无记录")}
            </p>


            <p>
                <b>发现地点：</b>
                ${escapeHtml(cat["发现地点"] || "暂无记录")}
            </p>


            <p>
                <b>毛色：</b>
                ${escapeHtml(cat["毛色"] || "暂无记录")}
            </p>


            <p>
                <b>体型：</b>
                ${escapeHtml(cat["体型"] || "暂无记录")}
            </p>


            <p>
                <b>性格：</b>
                ${escapeHtml(cat["性格"] || "暂无记录")}
            </p>


            <p>
                <b>常见行为：</b>
                ${escapeHtml(cat["常见行为"] || "暂无记录")}
            </p>


            <p>
                <b>备注：</b>
                ${escapeHtml(cat["备注"] || "暂无记录")}
            </p>


            <h2>
                📖《猫苑》关联记录
            </h2>

    `;


    // ==================================================
    // 《猫苑》关联记录
    // ==================================================

    if (
        Array.isArray(cat["猫苑评价"])
        &&
        cat["猫苑评价"].length > 0
    ) {


        cat["猫苑评价"].forEach(item => {


            // ==========================================
            // 判断理由
            // ==========================================

            let reasons = "";


            if (
                Array.isArray(item["判断理由"])
                &&
                item["判断理由"].length > 0
            ) {

                reasons =
                    item["判断理由"].join("；");

            }


            // ==========================================
            // 语义分数
            // ==========================================

            let semanticScore =
                item["语义分数"];


            if (
                typeof semanticScore === "number"
            ) {

                semanticScore =
                    semanticScore.toFixed(4);

            } else {

                semanticScore =
                    "暂无";

            }


            // ==========================================
            // 辅助证据
            // ==========================================

            let evidence =
                item["辅助证据"];


            if (
                evidence === undefined
                ||
                evidence === null
            ) {

                evidence = "暂无";

            }


            // ==========================================
            // 最终分数
            // ==========================================

            let finalScore =
                item["最终分数"];


            if (
                typeof finalScore === "number"
            ) {

                finalScore =
                    finalScore.toFixed(4);

            } else {

                finalScore =
                    "暂无";

            }


            // ==========================================
// 对外展示《猫苑》关联记录
// 只展示：特征类型 + 《猫苑》原文
// ==========================================

html += `

    <div class="record maoyuan-record">

        <p>
            <b>特征类型：</b>
            ${escapeHtml(
                item["特征类型"] || "暂无"
            )}
        </p>

        <p>
            <b>《猫苑》原文：</b>
        </p>

        <div class="maoyuan-text">

            ${escapeHtml(
                item["原文"] || "暂无原文"
            )}

        </div>

    </div>

`;

        });


    } else {


        // ==========================================
        // 没有匹配到《猫苑》
        // ==========================================

        html += `

            <div class="record">

                <p>
                    暂无《猫苑》相关记录
                </p>

            </div>

        `;

    }


    // ==================================================
    // 关闭猫咪详情 record
    // ==================================================

    html += `

        </div>

    `;


    // ==================================================
    // 显示结果
    // ==================================================

    result.innerHTML = html;

}




// ======================================================
// HTML 安全处理
// ======================================================

// 防止猫咪名称、行为等文字中出现特殊字符
// 导致网页结构被破坏

function escapeHtml(text) {

    if (text === undefined || text === null) {

        return "";

    }


    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}




// ======================================================
// HTML 属性安全处理
// ======================================================

function escapeHtmlAttribute(text) {

    return escapeHtml(text);

}

// =========================
// 自动生成校园猫咪地图标记
// =========================

async function loadMapMarkers(catList = cats) {

    const markerContainer =
        document.getElementById("mapMarkers");

    if (!markerContainer) {
        return;
    }

    try {

        const response =
            await fetch("map_areas.json");

        if (!response.ok) {
            throw new Error("地图区域数据读取失败");
        }

        const mapAreas =
            await response.json();


        // 清空旧标记
        markerContainer.innerHTML = "";

        // ============================================================
// 显示地图标准地点标签
// ============================================================

const standardPlaces = {};

Object.keys(mapAreas).forEach(areaName => {

    const position = mapAreas[areaName];

    if (!position) {
        return;
    }

    const standardPlace =
        position["地图标准地点"];

    if (!standardPlace) {
        return;
    }

    // 同一个标准地点只显示一次
    if (standardPlaces[standardPlace]) {
        return;
    }

    standardPlaces[standardPlace] = true;

    const placeLabel =
        document.createElement("div");

    placeLabel.className =
        "map-standard-place";

    placeLabel.style.left =
        `${position.x}%`;

    placeLabel.style.top =
        `${position.y}%`;

    placeLabel.innerHTML = `
        <div class="map-standard-dot">
            📍
        </div>

        <div class="map-standard-name">
            ${escapeHtml(standardPlace)}
        </div>
    `;

    markerContainer.appendChild(placeLabel);

});


        // 记录同一区域有几只猫
        const areaCount = {};


       catList.forEach(cat => {

            const area =
                cat["活动区域"];

            const position =
                mapAreas[area];


            // 如果数据库里的活动区域
            // 还没有设置地图坐标
            // 就暂时不显示
            if (!area || !position) {
                return;
            }


            if (!areaCount[area]) {
                areaCount[area] = 0;
            }


            const index =
                areaCount[area];

            areaCount[area]++;


           // ============================================================
// 同一区域多只猫：围绕地图标准地点环形展开
// ============================================================

let offsetX = 0;
let offsetY = 0;

if (index > 0) {

    // 从第二只猫开始围绕中心点排列
    const angle =
        (index - 1) * (Math.PI / 3);

    // 猫咪距离中心点的像素距离
    const radius = 28;

    offsetX =
        Math.cos(angle) * radius;

    offsetY =
        Math.sin(angle) * radius;

}


            const marker =
                document.createElement("div");


            marker.className =
                "map-cat-marker";


            marker.style.left =
                `calc(${position.x}% + ${offsetX}px)`;


            marker.style.top =
                `calc(${position.y}% + ${offsetY}px)`;


          marker.innerHTML = `
    <div class="map-cat-icon">
        🐱
    </div>

    <div class="map-cat-name">
        ${escapeHtml(cat["名字"] || "猫咪")}
    </div>

    <div class="map-cat-info">

        ${
            cat["毛色"]
            ?
            `<div>🎨 ${escapeHtml(cat["毛色"])}</div>`
            :
            ""
        }

        ${
            cat["性格"]
            ?
            `<div>💕 ${escapeHtml(cat["性格"])}</div>`
            :
            ""
        }

        ${
            cat["活动区域"]
            ?
            `<div>📍 ${escapeHtml(cat["活动区域"])}</div>`
            :
            ""
        }

        <div class="map-cat-hint">
            点击查看完整档案
        </div>

    </div>
`;


            // 点击猫咪 → 进入档案页
            marker.addEventListener(
                "click",
                function() {

                    window.location.href =
                        `detail.html?id=${cat.id}`;

                }
            );


            marker.title =
                `查看 ${cat["名字"] || "这只猫咪"} 的档案`;
            marker.addEventListener(
    "mouseenter",
    function() {

        marker.classList.add(
            "map-cat-hover"
        );

    }
);

marker.addEventListener(
    "mouseleave",
    function() {

        marker.classList.remove(
            "map-cat-hover"
        );

    }
);


            markerContainer.appendChild(marker);

        });

    }

    catch (error) {

        console.error(
            "地图猫咪标记加载失败：",
            error
        );

    }
}

// ============================================================
// 首页视图切换
// 猫咪图鉴 / 校园地图
// ============================================================

function showCatView() {

    const catView =
        document.getElementById("catList");

    const mapView =
        document.getElementById("mapView");

    const catButton =
        document.getElementById("catViewButton");

    const mapButton =
        document.getElementById("mapViewButton");


    // 显示猫咪图鉴
    if (catView) {
        catView.style.display = "";
    }

    // 隐藏地图
    if (mapView) {
        mapView.classList.add(
            "map-view-hidden"
        );
    }


    // 更新按钮状态
    if (catButton) {
        catButton.classList.add("active");
    }

    if (mapButton) {
        mapButton.classList.remove("active");
    }

}


function showMapView() {

    const catView =
        document.getElementById("catList");

    const mapView =
        document.getElementById("mapView");

    const catButton =
        document.getElementById("catViewButton");

    const mapButton =
        document.getElementById("mapViewButton");


    // 隐藏猫咪图鉴
    if (catView) {
        catView.style.display = "none";
    }

    // 显示地图
    if (mapView) {
        mapView.classList.remove(
            "map-view-hidden"
        );
    }


    // 更新按钮状态
    if (catButton) {
        catButton.classList.remove("active");
    }

    if (mapButton) {
        mapButton.classList.add("active");
    }


    // 重新加载地图
    loadMapMarkers();

}