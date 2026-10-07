let cats = [];


// 读取猫咪数据
fetch("cats_detail.json")
    .then(response => {

        if (!response.ok) {
            throw new Error("猫咪数据读取失败");
        }

        return response.json();
    })

    .then(data => {

        cats = data;

        showDetail();
    })

    .catch(error => {

        console.error(error);

        document.getElementById("detail").innerHTML = `
            <div class="cat-card">
                <h2>暂时无法读取猫咪档案</h2>
                <p>请检查 cats_detail.json 是否存在。</p>
            </div>
        `;
    });


// 显示猫咪档案
function showDetail() {

    // 获取网址中的 id
    let id = new URLSearchParams(
        window.location.search
    ).get("id");


    // 查找对应猫咪
    let cat = cats.find(
        item => String(item.id) === String(id)
    );


    // 没找到
    if (!cat) {

        document.getElementById("detail").innerHTML = `
            <div class="cat-card">
                <h2>没有找到这只猫咪</h2>
                <p>请返回猫咪图鉴重新选择。</p>

                <button onclick="goBack()">
                    ← 返回猫咪图鉴
                </button>
            </div>
        `;

        return;
    }


    // 开始生成档案
    let html = `

        <div class="cat-card cat-detail-card">

            <img
                class="big-img"
                src="images/${escapeHtmlAttribute(cat["照片"] || "default.jpg")}"
                onerror="this.onerror=null; this.src='images/default.jpg';"
            >


            <h1>
                🐱 ${escapeHtml(cat["名字"] || "未命名猫咪")}
            </h1>


            <div class="cat-basic-info">
            
                 <div class="cat-tags">

    ${
        cat["毛色"]
        ?
        `<span class="cat-tag">🎨 ${escapeHtml(cat["毛色"])}</span>`
        :
        ""
    }

    ${
        cat["体型"]
        ?
        `<span class="cat-tag">📏 ${escapeHtml(cat["体型"])}</span>`
        :
        ""
    }

    ${
        cat["性格"]
        ?
        `<span class="cat-tag">💕 ${escapeHtml(cat["性格"])}</span>`
        :
        ""
    }

</div>
               

                <p>
                    📍 <b>活动区域：</b>
                    ${escapeHtml(cat["活动区域"] || "暂无")}
                </p>


                <p>
                    🎨 <b>毛色：</b>
                    ${escapeHtml(cat["毛色"] || "暂无")}
                </p>


                <p>
                    📏 <b>体型：</b>
                    ${escapeHtml(cat["体型"] || "暂无")}
                </p>


                <p>
                    💕 <b>性格：</b>
                    ${escapeHtml(cat["性格"] || "暂无")}
                </p>


                <p>
                    🐾 <b>常见行为：</b>
                    ${escapeHtml(cat["常见行为"] || "暂无")}
                </p>


                <p>
                    📍 <b>发现地点：</b>
                    ${escapeHtml(cat["发现地点"] || "暂无")}
                </p>


                ${
                    cat["备注"]
                    ?
                    `
                    <p>
                        📝 <b>备注：</b>
                        ${escapeHtml(cat["备注"])}
                    </p>
                    `
                    :
                    ""
                }

            </div>


            <h2 class="section-title">
                📖 《猫苑》中的${escapeHtml(cat["名字"] || "这只猫")}
            </h2>

    `;


    // 《猫苑》关联记录
    if (
        Array.isArray(cat["猫苑评价"]) &&
        cat["猫苑评价"].length > 0
    ) {

        cat["猫苑评价"].forEach(item => {

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

        html += `

            <div class="record maoyuan-record">

                <p>
                    暂时还没有找到与这只猫咪对应的
                    《猫苑》记录。
                </p>

            </div>

        `;
    }


    html += `

            <button
                class="back-button"
                onclick="goBack()"
            >
                ← 返回猫咪图鉴
            </button>

        </div>

    `;


    document.getElementById("detail").innerHTML = html;
}



// 返回首页
function goBack() {

    window.location.href = "index.html";
}



// 防止特殊字符直接进入 HTML
function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function escapeHtmlAttribute(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}